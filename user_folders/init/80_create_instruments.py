print '80_create_instruments'
example1 = qt.instruments.create('example1', 'example', address='GPIB::1', reset=True)
dsgen = qt.instruments.create('dsgen', 'dummy_signal_generator')
pos = qt.instruments.create('pos', 'dummy_positioner')
