#=========================================================================
# DataMemXbar
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc, MemResponderIfc
from pymtl3.stdlib.mem         import mk_mem_msg

class DataMemXbar( VerilogPlaceholder, Component ):
  def construct( s ):

    DmemReqType, DmemRespType = mk_mem_msg( 8, 32, 32 )
    XmemReqType, XmemRespType = mk_mem_msg( 8, 32, 32 )
    MemReqType,  MemRespType  = mk_mem_msg( 8, 32, 32 )

    s.dmem = MemResponderIfc( DmemReqType, DmemRespType )
    s.xmem = MemResponderIfc( XmemReqType, XmemRespType )
    s.mem  = MemRequesterIfc( MemReqType,  MemRespType  )

