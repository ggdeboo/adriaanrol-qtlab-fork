print '80_create_instruments'

# example1 = qt.instruments.create('example1', 'example', address='GPIB::1', reset=True)
# dsgen = qt.instruments.create('dsgen', 'dummy_signal_generator')
# pos = qt.instruments.create('pos', 'dummy_positioner')

# Create a user instrument from the user ins directory
example_user_ins = qt.instruments.create('example_user_ins', 'example',
                                         address='GPIB::1')


example_def_instr = qt.instruments.create('example_def_instr',
                                          'dummy_signal_generator')


