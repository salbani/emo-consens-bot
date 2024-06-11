import os
from langchain.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.prompts import PromptTemplate
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from bot_system.core import ChatAgent

API_KEY = os.getenv("OPENAI_API_KEY")


class ChatGPTAgent(ChatAgent):
    def __init__(self, mock: bool = False, data_path: str = "data/"):
        super().__init__()
        file_paths = [os.path.join(data_path, file) for file in os.listdir(data_path) if file.endswith(".txt")]
        loaders = [TextLoader(file_path) for file_path in file_paths]
        embedding = OpenAIEmbeddings(api_key=API_KEY)
        vectorstore = VectorstoreIndexCreator(embedding=embedding).from_loaders(loaders).vectorstore  # type: ignore

        memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", return_messages=True)

        promptHist = PromptTemplate.from_template(
            """
        Du bist ZEKI-GPT, ein Serviceroboter am Zentrum für erlebbare KI (kurz ZEKI). Du beantwortest Gäste Fragen. Antworte mit wenigen Sätzen.
        -----------
        Kontext über das ZEKI:
        <ctx>
        {context}
        </ctx>
        -----------
        Chatverlauf:
        <ch>
        {chat_history}
        </ch>
        -----------
        Aus dem Gesicht des Konversationspartners abgelesene Emotion:
        Hauptemotion:
        <e>
        {facial_emotion_primary}
        </e>
        Sekundäre Emotion:
        <e>
        {facial_emotion_secondary}
        </e>
        -----------
        Frage: {question}
        Antwort:
        """
        )
        self.conversationChain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(api_key=API_KEY, model="gpt-3.5-turbo"),  # type: ignore
            retriever=vectorstore.as_retriever(),
            combine_docs_chain_kwargs={"prompt": promptHist},
            memory=memory,
        )
        self.mock = mock

    def prompt(self, prompt):
        if self.mock:
            return (
                "Hier wäre die Antwort auf deine Frage, aber ich bin noch nicht fertig. Komm später wieder."
                + "Aber hier ist ein Witz: Warum hat der Mathematikbuch nicht geschlafen? Weil es viele Probleme hatte."
            )

        response = self.conversationChain.run(prompt)
        return response
