########################################################################################################################
#
# Connection Factories
#
# Add definitions and imports of connection factories in this section and add them to the global dictionary of
# connection factories. Choose a short, indicative key, one that will be easy to identify and type in a user menu.

from pydcomm.connections.dummy import DummyConnectionFactory

# noinspection PyDictCreation
all_connection_factories = {}

#
# Example:
#   class MyConnectionFactory(ConnectionFactory):
#       ...
#
#   all_connection_factories["mine"] = MyConnectionFactory
#

all_connection_factories['dummy'] = DummyConnectionFactory
