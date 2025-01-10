# -*- coding: utf-8 -*-
# Copyright 2023 OpenSPG Authors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.


import json
from openai import OpenAI
import logging

from kag.interface import LLMClient
from tenacity import retry, stop_after_attempt

logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


@LLMClient.register("maas")
@LLMClient.register("openai")
class OpenAIClient(LLMClient):
    """
    A client class for interacting with the OpenAI API.

    Initializes the client with an API key, base URL, streaming option, temperature parameter, and default model.

    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        stream: bool = False,
        temperature: float = 0.7,
        timeout: float = None,
    ):
        """
        Initializes the OpenAIClient instance.

        Args:
            api_key (str): The API key for accessing the OpenAI API.
            base_url (str): The base URL for the OpenAI API.
            model (str): The default model to use for requests.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            temperature (float, optional): The temperature parameter for the model. Defaults to 0.7.
            timeout (float): The timeout duration for the service request. Defaults to None, means no timeout.
        """

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.stream = stream
        self.temperature = temperature
        self.timeout = timeout
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.check()

    def __call__(self, prompt: str, image_url: str = None):
        """
        Executes a model request when the object is called and returns the result.

        Parameters:
            prompt (str): The prompt provided to the model.

        Returns:
            str: The response content generated by the model.
        """
        # Call the model with the given prompt and return the response
        if image_url:
            message = [
                {"role": "system", "content": "you are a helpful assistant"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                stream=self.stream,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            rsp = response.choices[0].message.content
            return rsp

        else:
            message = [
                {"role": "system", "content": "you are a helpful assistant"},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                stream=self.stream,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            rsp = response.choices[0].message.content
            return rsp

    @retry(stop=stop_after_attempt(3))
    def call_with_json_parse(self, prompt):
        """
        Calls the model and attempts to parse the response into JSON format.

        Parameters:
            prompt (str): The prompt provided to the model.

        Returns:
            Union[dict, str]: If the response is valid JSON, returns the parsed dictionary; otherwise, returns the original response.
        """
        # Call the model and attempt to parse the response into JSON format
        rsp = self(prompt)
        _end = rsp.rfind("```")
        _start = rsp.find("```json")
        if _end != -1 and _start != -1:
            json_str = rsp[_start + len("```json") : _end].strip()
        else:
            json_str = rsp
        try:
            json_result = json.loads(json_str)
        except:
            return rsp
        return json_result
