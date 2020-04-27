"""
Rest Joint database example.
"""

# See: https://docs.sqlalchemy.org/en/13/orm/tutorial.html

from sqlalchemy import *
from sqlalchemy import orm
from sqlalchemy.ext import declarative
from datetime import datetime

# SQLA engine, session and declarative_base
uri = "sqlite:////tmp/rest-joint-example.sqlite"  # FIXME: /tmp is wiped on reboots
engine = create_engine(uri, echo=True)
Session = orm.sessionmaker(bind=engine)
Base = declarative.declarative_base()
# metadata = MetaData()

# Database tables definition
nn_tag_event = Table("nn_tag_event", Base.metadata,
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
    Column("event_id", ForeignKey("event.id"), primary_key=True))

class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    color = Column(String, default=None)

    event = orm.relationship("Event", back_populates="tag", secondary=nn_tag_event)

class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    summary = Column(String, nullable=False)
    description = Column(String)
    time = Column(DateTime, default=datetime.utcnow)

    tag = orm.relationship("Tag", back_populates="event", secondary=nn_tag_event, lazy='joined')


# Data population:

def populate():
    """
    Drop and create database schema and populate a example dataset for development purpose.
    """

    from faker import Faker
    import math

    fake = Faker("fr_FR")  # french touch
    def generate(kind, n=10):
        """
        Return `n` unique words of the given `kind`, which is a Faker provider.
        """
        if (not hasattr(fake, kind)):
            kinds = [k for k in dir(fake)
                if not k.startswith("_") and k not in ["add_provider", "random", "factories"]]
            raise ValueError(f"Invaid kind '{kind}', try one of {kinds}")

        items = set()
        while len(items) < n:
            items.add(getattr(fake, kind)())

        return items

    def distribute(child, parent):

        children = records[child]
        parents = records[parent]

        per_parent = len(children) / len(parents)

        if per_parent < 1:
            # the logic below only works with a number of children > parents
            # simply invert everything to chunk the given parents instead of the given children children
            children, parents = parents, children
            parent, child = child, parent
            per_parent = 1 / per_parent

        print(f'\nDistributing children "{child}" to parents "{parent}":')
        for shift, parent_record in enumerate(parents):
            # floor will make leftover children, but never a lack for a parent
            chunksize = math.floor(per_parent)
            lo = chunksize * shift
            up = chunksize * (shift + 1)

            if shift == len(parents) - 1:
                # last iteration: include the potential remaining children from floor
                # there is a better a method of quatization
                up = len(children)

            print(f'adding ({lo}:{up}) {up-lo}/{len(children)} children "{child}" to parent "{parent}" {shift+1}/{len(parents)}')#' ({parent_record})')
            relation = getattr(parent_record, child)
            relation.extend(children[lo:up])

    # Just populate it it

    n_tag = 100
    n_event = 1000

    records = dict(
        tag=[Tag(name=word)
            for word in generate('word', n_tag)],

        event=[Event(
            summary=sentence.strip('.'),
            description=paragraph,
            time=datetime_)
                for sentence, paragraph, datetime_
                in zip(
                    generate('sentence', n_event),
                    generate('text', n_event),
                    generate('date_time', n_event))])

    print(', '.join(f'{len(records[model])} {model}' for model in records.keys()))

    # Call to distribute() could be automated by (discovering or) giving a relationship structure, eg:
    # structure = dict(tag = dict(event = dict(... = dict(...),
    #                                          ... = dict(...))))
    distribute('tag', 'event')
    dataset = [record for model, records in records.items() for record in records]

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session = Session()
    for record in dataset:
        session.add(record)

    session.commit()