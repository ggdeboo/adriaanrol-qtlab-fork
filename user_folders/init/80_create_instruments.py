# Create a user instrument from the user ins directory
example_user_ins = qt.instruments.create('example_user_ins', 'example',
                                         address='GPIB::1',
                                         dummy_instrument=True)
# And create a default instrument from the qtlab instruments

example_def_instr = qt.instruments.create('example_def_instr',
                                          'dummy_signal_generator',
                                          dummy_instrument=True)


