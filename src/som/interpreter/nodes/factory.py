from som.interpreter.nodes.enforced.field_node import EnforcedFieldReadNode, \
    EnforcedFieldWriteNode
from som.interpreter.nodes.field_node import get_read_node_class, \
    get_write_node_class, UnenforcedFieldReadNodeN, UnenforcedFieldWriteNodeN
from som.vmobjects.object import Object


def create_read_node(self_exp_en, self_exp_un, index, universe):
    if index < Object.NUMBER_OF_DIRECT_FIELDS:
        return EnforcedFieldReadNode(self_exp_en, index, universe), \
               get_read_node_class(index)(self_exp_un)
    else:
        return EnforcedFieldReadNode(self_exp_en, index, universe), \
               UnenforcedFieldReadNodeN(self_exp_un,
                                        index - Object.NUMBER_OF_DIRECT_FIELDS)


def create_write_node(self_en, self_un, index, value_en, value_un, universe):
    if index < Object.NUMBER_OF_DIRECT_FIELDS:
        return EnforcedFieldWriteNode(self_en, index, value_en, universe), \
               get_write_node_class(index)(self_un, value_un)
    else:
        return EnforcedFieldWriteNode(self_en, index, value_en, universe), \
               UnenforcedFieldWriteNodeN(self_un, value_un,
                                         index - Object.NUMBER_OF_DIRECT_FIELDS)
