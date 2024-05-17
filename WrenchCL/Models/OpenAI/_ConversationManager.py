#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#
try:
    from colorama import Fore, Style
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

from openai import AssistantEventHandler, OpenAI
from ...Tools.WrenchLogger import logger


class EventHandler(AssistantEventHandler):
    """
    Custom event handler for OpenAI Assistant that handles text and tool call events, printing them with colored output.
    """

    def on_text_created(self, text) -> None:
        """
        Called when the assistant creates text. Prints the text with a specific color.

        :param text: The created text.
        :type text: str
        """
        print(f"{Fore.CYAN if COLORAMA_AVAILABLE else ''}\nassistant > ", end="", flush=True)

    def on_text_delta(self, delta, snapshot):
        """
        Called when there is a delta in the text. Prints the delta text with a specific color.

        :param delta: The delta text.
        :type delta: TextDelta
        :param snapshot: The snapshot of the current state.
        :type snapshot: dict
        """
        print(f"{Fore.YELLOW if COLORAMA_AVAILABLE else ''}{delta.value}", end="", flush=True)

    def on_tool_call_created(self, tool_call):
        """
        Called when a tool call is created. Prints the tool call type with a specific color.

        :param tool_call: The created tool call.
        :type tool_call: CodeInterpreterToolCall | FileSearchToolCall | FunctionToolCall
        """
        print(f"{Fore.GREEN if COLORAMA_AVAILABLE else ''}\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        """
        Called when there is a delta in the tool call. Prints the tool call input and outputs with specific colors.

        :param delta: The delta tool call.
        :type delta: CodeInterpreterToolCallDelta | FileSearchToolCallDelta | FunctionToolCallDelta
        :param snapshot: The snapshot of the current state.
        :type snapshot: dict
        """
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(f"{Fore.MAGENTA if COLORAMA_AVAILABLE else ''}{delta.code_interpreter.input}", end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"{Fore.GREEN if COLORAMA_AVAILABLE else ''}\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"{Fore.WHITE if COLORAMA_AVAILABLE else ''}\n{output.logs}", flush=True)


class ConversationManager:
    """
    Manages conversation threads with the OpenAI Assistant, including adding messages, creating threads,
    and streaming responses.
    """

    def __init__(self, client, assistant_id=None):
        """
        Initializes the ConversationManager with a client and optional assistant ID.

        :param client: The OpenAI client.
        :type client: OpenAI
        :param assistant_id: The assistant ID, if any.
        :type assistant_id: str, optional
        """
        self.client = client
        self.assistant_id = assistant_id

    def add_message_to_thread(self, thread_id, text):
        """
        Adds a message to an existing conversation thread.

        :param thread_id: The ID of the thread.
        :type thread_id: str
        :param text: The message text to add.
        :type text: str
        """
        self.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=text)

    def create_thread(self):
        """
        Creates a new conversation thread and returns its ID.

        :returns: The ID of the created thread.
        :rtype: str
        """
        thread = self.client.beta.threads.create()
        logger.info(f"{Fore.BLUE if COLORAMA_AVAILABLE else ''}Thread created with ID: {thread.id}")
        return thread.id

    def stream_responses(self, thread_id):
        """
        Streams responses using the AssistantEventHandler.

        :param thread_id: The ID of the thread to stream responses for.
        :type thread_id: str
        """
        with self.client.beta.threads.runs.stream(thread_id=thread_id, assistant_id=self.assistant_id,
                                                  event_handler=EventHandler()) as stream:
            stream.until_done()

    def initiate_conversation(self):
        """
        Initiates and manages a conversation until the user exits. Continuously streams responses and captures user input.
        """
        try:
            thread_id = self.create_thread()

            while True:
                self.stream_responses(thread_id)
                user_input = input(f"{Fore.LIGHTBLUE_EX if COLORAMA_AVAILABLE else ''}\nYou: {Style.RESET_ALL}")
                if user_input.lower() == 'exit':
                    print(f"{Fore.RED if COLORAMA_AVAILABLE else ''}Exiting conversation.")
                    break
                self.add_message_to_thread(thread_id, user_input)

        except Exception as e:
            logger.error(f"{Fore.RED if COLORAMA_AVAILABLE else ''}Error in initiating conversation: {str(e)}")
            raise
