//=========================================================================
// DataMemXbar
//=========================================================================

`ifndef PMX_DATA_MEM_XBAR_V
`define PMX_DATA_MEM_XBAR_V

`include "vc/mem-msgs.v"
`include "vc/queues.v"
`include "vc/trace.v"

module pmx_v2_DataMemXbar
(
  input  logic          clk,
  input  logic          reset,

  // Processor Data Memory Interface

  input  mem_req_4B_t   dmem_reqstream_msg,
  input  logic          dmem_reqstream_val,
  output logic          dmem_reqstream_rdy,

  output mem_resp_4B_t  dmem_respstream_msg,
  output logic          dmem_respstream_val,
  input  logic          dmem_respstream_rdy,

  // Xcel Memory Interface

  input  mem_req_4B_t   xmem_reqstream_msg,
  input  logic          xmem_reqstream_val,
  output logic          xmem_reqstream_rdy,

  output mem_resp_4B_t  xmem_respstream_msg,
  output logic          xmem_respstream_val,
  input  logic          xmem_respstream_rdy,

  // Main Memory Interface

  output mem_req_4B_t   mem_reqstream_msg,
  output logic          mem_reqstream_val,
  input  logic          mem_reqstream_rdy,

  input  mem_resp_4B_t  mem_respstream_msg,
  input  logic          mem_respstream_val,
  output logic          mem_respstream_rdy
);

  //----------------------------------------------------------------------
  // Last Granted Request Register
  //----------------------------------------------------------------------
  // 01 means last granted request went to dmem
  // 10 means last granted request went to xmem

  logic [1:0] last_granted_req, granted_req;

  always_ff @( posedge clk ) begin

    if ( reset )
      last_granted_req <= 2'b01;

    // Only update the register if there is a new granted request

    else if ( |granted_req )
      last_granted_req <= granted_req;

  end

  //----------------------------------------------------------------------
  // Crossbar Request Logic
  //----------------------------------------------------------------------

  always_comb begin

    mem_reqstream_val = '0;
    mem_reqstream_msg = '0;
    granted_req       = '0;

    // Only dmem is making a request

    if ( dmem_reqstream_val && !xmem_reqstream_val )
      granted_req = 2'b01;

    // Only xmem is making a request

    else if ( !dmem_reqstream_val && xmem_reqstream_val )
      granted_req = 2'b10;

    // Both dmem and xmem are making requests, so arbitrate such that
    // the granted request is opposite of last granted request

    else if ( dmem_reqstream_val && xmem_reqstream_val ) begin
      if ( last_granted_req == 2'b01 )
        granted_req = 2'b10;
      else
        granted_req = 2'b01;
    end

    // Update outputs if granted request is for dmem, store the requester
    // in the opaque field so we can route the response correctly

    if ( granted_req == 2'b01 ) begin
      mem_reqstream_msg        = dmem_reqstream_msg;
      mem_reqstream_msg.opaque = 1'b0;
      mem_reqstream_val        = 1'b1;
    end

    // Update outputs if granted request is for xmem, store the requester
    // in the opaque field so we can route the response correctly

    if ( granted_req == 2'b10 ) begin
      mem_reqstream_msg        = xmem_reqstream_msg;
      mem_reqstream_msg.opaque = 1'b1;
      mem_reqstream_val        = 1'b1;
    end

  end

  // Request ready logic - note how dmem_reqstream_rdy does not depend on
  // dmem_reqstream_val and dmem_reqstream_rdy does not depend on
  // xmem_reqstream_val to try and avoid combinational loops.

  assign dmem_reqstream_rdy
    = mem_reqstream_rdy && (!xmem_reqstream_val || (last_granted_req == 2'b10));

  assign xmem_reqstream_rdy
    = mem_reqstream_rdy && (!dmem_reqstream_val || (last_granted_req == 2'b01));

  //----------------------------------------------------------------------
  // Crossbar Response Logic
  //----------------------------------------------------------------------

  // Response valid logic - note how dmem_respstream_val does not depend
  // on dmem_respstream_rdy and xmem_responstream_val does not depend on
  // xmem_respstream_rdy.

  always_comb begin

    dmem_respstream_val = '0;
    xmem_respstream_val = '0;

    if ( mem_respstream_val ) begin

      // Response should go to dmem

      if ( mem_respstream_msg.opaque == 1'b0 )
        dmem_respstream_val = 1'b1;

      // Response should go to xmem

      if ( mem_respstream_msg.opaque == 1'b1 )
        xmem_respstream_val = 1'b1;

    end

  end

  // Response ready logic - note that mem_respstream_rdy _does_ depend on
  // mem_respstream_val ... but there is nothing we can do about this. We
  // need the opaque field to route the response and we have to know if
  // the response field is valid.

  always_comb begin

    mem_respstream_rdy = '0;

    if ( mem_respstream_val ) begin

      // Main memory ready depends on dmem ready

      if ( mem_respstream_msg.opaque == 1'b0 )
        mem_respstream_rdy = dmem_respstream_rdy;

      // Main memory ready depends on xmem ready

      if ( mem_respstream_msg.opaque == 1'b1 )
        mem_respstream_rdy = xmem_respstream_rdy;

    end

  end

  // Main memory response message is directly connected to the dmem and
  // xmem response message (make sure to zero out the opaque field)

  always_comb begin
    dmem_respstream_msg = mem_respstream_msg;
    dmem_respstream_msg.opaque = '0;
    xmem_respstream_msg = mem_respstream_msg;
    xmem_respstream_msg.opaque = '0;
  end

endmodule

`endif /* PMX_DATA_MEM_XBAR_V */

