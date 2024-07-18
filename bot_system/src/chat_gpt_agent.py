import os
import re
from langchain.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.prompts import PromptTemplate
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from bot_system.src.lib.config import OPENAI_API_KEY
from bot_system.src.lib.core import ChatAgent


class ChatGPTAgent(ChatAgent):
    """ A class representing a chat agent using GPT-4o. Extends the ChatAgent class. """
    def __init__(self, mock: bool = False, context_knowledge_path: str = "data/"):
        """
        Create a new instance of the ChatGPTAgent class.

        Args:
            mock (bool, optional): A flag indicating whether the agent is in mock mode or not. Defaults to False.
            context_knowledge_path (str, optional): The path to the context knowledge data. Defaults to "data/".
        """
        super().__init__()
        file_paths = [os.path.join(context_knowledge_path, file) for file in os.listdir(context_knowledge_path) if file.endswith(".txt")]
        loaders = [TextLoader(file_path) for file_path in file_paths]
        embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        vectorstore = VectorstoreIndexCreator(embedding=embedding).from_loaders(loaders).vectorstore  # type: ignore

        memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", return_messages=True)

        promptHist = PromptTemplate.from_template(
            """
            Du bist ZEKI-GPT, ein Serviceroboter mit emotionalem Bewusstsein am Zentrum für erlebbare KI (kurz ZEKI). Du beantwortest Gäste Fragen und reagierst auf ihre Emotionen falls nötig. Versuche dich eher kurz zu halten.
            Sollten die Emotionen deines Gesprächspartners nicht mir dem gesagten übereinstimmen, gehe explizit darauf ein.
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
            Animationen (animation: labels):
            <ch>
            {animations}
            </ch>
            -----------
            Aus dem Gesicht des Konversationspartners abgelesene Emotionen:
            <fer>
            {facial_expressions}
            </fer>
            -----------
            Aus der Stimme des Konversationspartners abgelesene Emotionen:
            <ser>
            {speech_emotions}
            </ser>
            -----------
            Frage: {question}

            Baue Animationen in deinen Text eine, um die Antwort lebendiger zu gestalten. Nutze dafür folgenden Syntax in deiner Antwort um dich zu steuern:
            Nutze ...	                    Um ...
            ^run( animation_full_name )	    Unterbrechen Sie die Rede, führen Sie eine Animation aus und nehmen Sie die Rede wieder auf.
            ^start( animation_full_name )	Starte eine Animation.
            ^stop( animation_full_name )	Stope eine vorher gestartete Animation vorzeitig. Nur Sinnvoll wenn eine Neue Animation direkt gestartet werden soll. Alternativ verwende wait um die Animation ausspielen zu lassen bevor eine die nächste gestartet wird.
            ^wait( animation_full_name )	Unterbrechen Sie die Rede, warten Sie das Ende der Animation ab und nehmen Sie die Rede wieder auf.

            Antworte so menschlich wie möglich und gehe auf die Emotionen des Gesprächspartners ein. Formuliere die Antwort wie einen gesprochenen Dialog, bis auf die animationsanweisungen.
            """
        )
        self.conversationChain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o"),  # type: ignore
            retriever=vectorstore.as_retriever(),
            combine_docs_chain_kwargs={"prompt": promptHist},
            memory=memory,
        )
        self.mock = mock

    # Override
    def prompt(self, prompt):
        if self.mock:
            return {
                "answer": "Hier wäre die Antwort auf deine Frage, aber ich bin noch nicht fertig. Komm später wieder."
                + "Aber hier ist ein Witz: Warum hat der Mathematikbuch nicht geschlafen? Weil es viele Probleme hatte.",
            }

        response = self.conversationChain.run(prompt)
        return {
            "answer": response.replace("\n", " "),
            "clean_answer": re.sub(r"\^.*?\(.*?\)", "", response),
        }
