#=========================================================================
# DataMemXbar_test
#=========================================================================

import pytest

from random import seed, randint

from pymtl3 import *

from pymtl3.stdlib.mem        import MemoryFL, mk_mem_msg, MemMsgType
from pymtl3.stdlib.stream     import StreamSourceFL, StreamSinkFL
from pymtl3.stdlib.test_utils import run_sim, mk_test_case_table

from pmx_v2.DataMemXbar import DataMemXbar

#-------------------------------------------------------------------------
# Message Types
#-------------------------------------------------------------------------

CacheReqType, CacheRespType = mk_mem_msg( 8, 32, 32 )
MemReqType,   MemRespType   = mk_mem_msg( 8, 32, 32 )

def req( type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT

  return CacheReqType( type_, opaque, addr, len, data)

def resp( type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT

  return CacheRespType( type_, opaque, test, len, data )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s ):

    # Instantiate models

    s.dsrc  = StreamSourceFL( CacheReqType )
    s.dsink = StreamSinkFL( CacheRespType )

    s.xsrc  = StreamSourceFL( CacheReqType )
    s.xsink = StreamSinkFL( CacheRespType )

    s.xbar  = DataMemXbar()
    s.mem   = MemoryFL( 1, [(CacheReqType,CacheRespType)] )

    # Connect

    s.dsrc.ostream    //= s.xbar.dmem.reqstream
    s.dsink.istream   //= s.xbar.dmem.respstream

    s.xsrc.ostream    //= s.xbar.xmem.reqstream
    s.xsink.istream   //= s.xbar.xmem.respstream

    s.xbar.mem        //= s.mem.ifc[0]

  def done( s ):
    return s.dsrc.done() and s.dsink.done() and \
           s.xsrc.done() and s.xsink.done()

  def line_trace( s ):
    return s.dsrc.line_trace() + "|" + s.xsrc.line_trace() + " > " \
         + s.mem.line_trace() + " > " \
         + s.dsink.line_trace() + "|" + s.xsink.line_trace()

#-------------------------------------------------------------------------
# basic_msgs0
#-------------------------------------------------------------------------

def basic_msgs0():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 0, 0x04030201 ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'wr', 0x0, 0x1004, 0, 0x08070605 ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'wr', 0x0, 0x1008, 0, 0x0c0b0a09 ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'wr', 0x0, 0x100c, 0, 0x0f0e0d0c ), resp( 'wr', 0x0, 0,   0,  0          ),

    req( 'rd', 0x0, 0x1000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x04030201 ),
    req( 'rd', 0x0, 0x1004, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x08070605 ),
    req( 'rd', 0x0, 0x1008, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x0c0b0a09 ),
    req( 'rd', 0x0, 0x100c, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x0f0e0d0c ),
  ]

#-------------------------------------------------------------------------
# basic_msgs1
#-------------------------------------------------------------------------

def basic_msgs1():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x2000, 0, 0x14131211 ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'wr', 0x0, 0x2004, 0, 0x18171615 ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'wr', 0x0, 0x2008, 0, 0x1c1b1a19 ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'wr', 0x0, 0x200c, 0, 0x1f1e1d1c ), resp( 'wr', 0x0, 0,   0,  0          ),

    req( 'rd', 0x0, 0x2000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x14131211 ),
    req( 'rd', 0x0, 0x2004, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x18171615 ),
    req( 'rd', 0x0, 0x2008, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x1c1b1a19 ),
    req( 'rd', 0x0, 0x200c, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x1f1e1d1c ),
  ]

#-------------------------------------------------------------------------
# random_msgs0
#-------------------------------------------------------------------------

def random_msgs0():

  seed(0xa4e28cc2)

  vmem = 16*[0]
  msgs = []

  # First write 16 addresses

  for i in range(0,16):
    vmem[i] = i
    msgs.extend([
      req( 'wr', 0, 0x00001000+4*i, 0, i ), resp( 'wr', 0, 0, 0, 0 ),
    ])

  # Now lots of random accesses

  for i in range(100):
    idx = randint(0,15)

    if randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', 0, 0x00001000+4*idx, 0, 0 ), resp( 'rd', 0, 0, 0, correct_data ),
      ])

    else:

      new_data = randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, 0x00001000+4*idx, 0, new_data ), resp( 'wr', 0, 0, 0, 0 ),
      ])

  # Read all data again to make sure every write was correct

  for i in range(0,16):
    correct_data = vmem[i]
    msgs.extend([
      req( 'rd', i, 0x00001000+4*i, 0, 0 ), resp( 'rd', 0, 0, 0, correct_data ),
    ])

  return msgs

#-------------------------------------------------------------------------
# random_msgs1
#-------------------------------------------------------------------------

def random_msgs1():

  seed(0xd76ac272)

  vmem = 16*[0]
  msgs = []

  # First write 16 addresses

  for i in range(0,16):
    vmem[i] = i
    msgs.extend([
      req( 'wr', 0, 0x00002000+4*i, 0, i ), resp( 'wr', 0, 0, 0, 0 ),
    ])

  # Now lots of random accesses

  for i in range(100):
    idx = randint(0,15)

    if randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', 0, 0x00002000+4*idx, 0, 0 ), resp( 'rd', 0, 0, 0, correct_data ),
      ])

    else:

      new_data = randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, 0x00002000+4*idx, 0, new_data ), resp( 'wr', 0, 0, 0, 0 ),
      ])

  # Read all data again to make sure every write was correct

  for i in range(0,16):
    correct_data = vmem[i]
    msgs.extend([
      req( 'rd', i, 0x00002000+4*i, 0, 0 ), resp( 'rd', 0, 0, 0, correct_data ),
    ])

  return msgs

#-------------------------------------------------------------------------
# run_test
#-------------------------------------------------------------------------

def run_test( test_params, cmdline_opts=None ):

  # Instantiate test harness

  th = TestHarness()

  # Generate messages

  dmsgs = test_params.msg0_func()
  xmsgs = test_params.msg1_func()

  # Set parameters

  th.set_param("top.dsrc.construct",
    msgs=dmsgs[::2],
    initial_delay=test_params.src+3,
    interval_delay=test_params.src )

  th.set_param("top.dsink.construct",
    msgs=dmsgs[1::2],
    initial_delay=test_params.sink+3,
    interval_delay=test_params.sink )

  th.set_param("top.xsrc.construct",
    msgs=xmsgs[::2],
    initial_delay=test_params.src+3,
    interval_delay=test_params.src )

  th.set_param("top.xsink.construct",
    msgs=xmsgs[1::2],
    initial_delay=test_params.sink+3,
    interval_delay=test_params.sink )

  th.set_param( "top.mem.construct",
    stall_prob=test_params.stall,
    extra_latency=test_params.lat )

  th.elaborate()

  # Run the test

  run_sim( th, cmdline_opts, duts=['xbar'] )

#-------------------------------------------------------------------------
# test
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                      "msg0_func     msg1_func     stall lat src sink"),
  [ "basic",              basic_msgs0,  basic_msgs1,  0.0,  0,  0,  0    ],
  [ "random",             random_msgs0, random_msgs1, 0.0,  0,  0,  0    ],
  [ "random_sink_delay1", random_msgs0, random_msgs1, 0.2,  0,  0,  1    ],
  [ "random_src_delay1",  random_msgs0, random_msgs1, 0.2,  0,  1,  0    ],
  [ "random_both_delay1", random_msgs0, random_msgs1, 0.2,  0,  1,  1    ],
  [ "random_sink_delay3", random_msgs0, random_msgs1, 0.5,  3,  0,  3    ],
  [ "random_src_delay3",  random_msgs0, random_msgs1, 0.5,  3,  3,  0    ],
  [ "random_both_delay3", random_msgs0, random_msgs1, 0.5,  3,  3,  3    ],
  [ "random_sink_delay8", random_msgs0, random_msgs1, 0.5,  3,  0,  8    ],
  [ "random_src_delay8",  random_msgs0, random_msgs1, 0.5,  3,  8,  0    ],
  [ "random_both_delay8", random_msgs0, random_msgs1, 0.5,  3,  8,  8    ],
])

@pytest.mark.parametrize( **test_case_table )
def test( test_params, cmdline_opts ):
  run_test( test_params, cmdline_opts )

