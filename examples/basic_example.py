"""
.. _basic_example:

Basic example of dpf composites usage
-------------------------------------

Very basic!
"""

out = "Hello World"

#####################
import ansys.dpf.core as dpf

# depending on your scenario you might also need to start the dpf server
# for instance server = dpf.start_local_server()
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
