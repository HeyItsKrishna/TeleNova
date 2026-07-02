from app.db.connection import database
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.billing_repository import BillingRepository
from app.db.repositories.network_repository import NetworkRepository
from app.db.repositories.ticket_repository import TicketRepository
from app.db.repositories.knowledge_repository import KnowledgeRepository


class RepositoryContainer:
    def __init__(self):
        self.accounts = AccountRepository(database)
        self.billing = BillingRepository(database)
        self.network = NetworkRepository(database)
        self.tickets = TicketRepository(database)
        self.knowledge = KnowledgeRepository(database)


repositories = RepositoryContainer()