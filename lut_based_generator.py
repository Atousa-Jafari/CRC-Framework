import sin


def generate_verilog_code(num_reservoir_neurons, input_weight, reservoir_state, a_scaled, b_scaled, c_scaled, d_scaled, reservoir_weight, output_weight):
    code = f"""`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company:
// Engineer:
//
// Create Date: 03/04/2024 09:10:17 AM
// Design Name:
// Module Name: EchoStateNetwork
// Project Name:
// Target Devices:
// Tool Versions:
// Description:
//
// Dependencies:
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
//////////////////////////////////////////////////////////////////////////////////

module ESN_Generator_V2(
    input clk,
    input signed [7:0] input_data,     // Q2.6 format
    output wire signed [31:0] output_data   // Q2.6 format
);
parameter num_reservoir_neurons = {num_reservoir_neurons};

// Reservoir layer
reg signed [15:0] a_scaled = 16'd{a_scaled};
reg signed [15:0] b_scaled = 16'd{b_scaled};
reg signed [15:0] c_scaled = 16'd{c_scaled};
reg signed [15:0] d_scaled = 16'd{d_scaled};
reg signed [31:0] reservoir_state [0: num_reservoir_neurons-1]; // Q4.12 format
initial begin
"""
    for i in range(num_reservoir_neurons):
        if i < num_reservoir_neurons - 1:
            if reservoir_state[0][i]<0:
                code += f"reservoir_state[{i}] = -16'sd{abs(reservoir_state[0][i])};\n"
            else:
                 code += f"reservoir_state[{i}] = 16'sd{reservoir_state[0][i]};\n"
        else:
            if reservoir_state[0][i]<0:
                code += f"reservoir_state[{i}] = -16'sd{abs(reservoir_state[0][i])};\n"
            else:
                code += f"reservoir_state[{i}] = 16'sd{abs(reservoir_state[0][i])};\n"

    code += """end

  // Scaling factors and zero point
  reg signed [31:0] scale = 32'b00000000000001011001011001000000;         // Q2.14 format

  reg signed [31:0] input_sum_parallel [0: num_reservoir_neurons-1];
  reg signed [31:0] reservoir_sum_parallel [0: num_reservoir_neurons-1];
  reg signed [31:0] output_sum;
  integer i,j,k,l,m;

  reg signed [31:0] reg_input [0: num_reservoir_neurons-1];
  reg signed [31:0] reg_reservoir [0: num_reservoir_neurons-1];
"""
    # for i in range(8):
    #     if i < 7:
    #         code += f"reg signed [31:0] shifted_input{i};\n"
    #     else:
    #         code += f"reg signed [31:0] shifted_input{i};\n"


    for i in range(num_reservoir_neurons):
        for j in range(num_reservoir_neurons):

            for bit in range(8):
                if (reservoir_weight[j][i] >> bit) & 1:
                    code += f"wire signed [31:0] shifted_state{i}_{j}_{bit} = reservoir_state[{j}] <<< {bit};\n"

    for i in range(num_reservoir_neurons):
        for bit in range(8):
            if (output_weight[i] >> bit) & 1:
                code += f"wire signed [31:0] shifted_state_out{i}_{bit} = reservoir_state[{i}] <<< {bit};\n"


    for i in range(8):
        if i < 7:
            code += f"wire signed [31:0] shifted_input{i} = input_data <<< {i};\n"
        else:
            code += f"wire signed [31:0] shifted_input{i} = input_data <<< {i};\n"

    code +="""
  // ESN logic
  always @(posedge clk) begin

"""



    for i in range(num_reservoir_neurons):
        input_mults = []
        for bit in range(8):
            if (input_weight[i] >> bit) & 1:
                input_mults.append(f"shifted_input{bit}")
        if input_mults:
          code += f"      input_sum_parallel[{i}] = " + " + ".join(input_mults) + ";\n"
        else:
          code += f"      input_sum_parallel[{i}] = 0" + ";\n"

    for i in range(num_reservoir_neurons):
        if i < num_reservoir_neurons-1:
            code += f"reservoir_sum_parallel[{i}] = 32'sd0;\n"
        else:
            code += f"reservoir_sum_parallel[{i}] = 32'sd0;\n"


    for i in range(num_reservoir_neurons):
        # code += f"      reservoir_sum_parallel[{i}] = 0;\n"
        reservoir_weight_mults = []
        for j in range(num_reservoir_neurons):

            for bit in range(8):
                if (reservoir_weight[j][i] >> bit) & 1:
                    reservoir_weight_mults.append(f"shifted_state{i}_{j}_{bit}")
        if reservoir_weight_mults:
          code += f"      reservoir_sum_parallel[{i}] = (" + " + ".join(reservoir_weight_mults) + ");\n"
        else:
          code += f"      reservoir_sum_parallel[{i}] = 0" + ";\n"

    code += """      // Threshold comparisons
      for (i = 0; i < num_reservoir_neurons; i = i + 1) begin
          reg_input[i] = 0;
          if (input_sum_parallel[i] < a_scaled) begin
              reg_input[i] = a_scaled;
         end
          else if (input_sum_parallel[i] > b_scaled) begin
              reg_input[i] = b_scaled;
          end
          else begin
              reg_input[i] = input_sum_parallel[i];
          end
      end

      for (k = 0; k < num_reservoir_neurons; k = k + 1) begin
          reg_reservoir[k] = 0;
          if (reservoir_sum_parallel[k] < c_scaled) begin
              reg_reservoir[i] = c_scaled;
          end
          else if (reservoir_sum_parallel[k] > d_scaled) begin
              reg_reservoir[k] = d_scaled;
          end
          else begin
              reg_reservoir[k] = reservoir_sum_parallel[k];
          end
      end


      for (j = 0; j < num_reservoir_neurons; j = j + 1) begin
      reg_input[j]=reg_input[j]+16'd1628;

          reg_input[j] = reg_input[j] >> 8;
          reg_reservoir[j]=reg_reservoir[j]+16'd17641;
          reg_reservoir[j]= reg_reservoir[j] >> 8;
      end

  // Store results in reservoir_states
      for (m = 0; m < num_reservoir_neurons; m = m + 1) begin
          reservoir_state[m] <= reg_reservoir[m] + reg_input[m]-255;
      end
"""

    code += """      // Output calculation
      output_sum = 0;
"""
    out_weight_mults = []
    for i in range(num_reservoir_neurons):

        for bit in range(8):
            if (output_weight[i] >> bit) & 1:
                out_weight_mults.append(f"shifted_state_out{i}_{bit}")
    code += f"      output_sum = output_sum + (" + " + ".join(out_weight_mults) + ");\n"

    code += """
    end
    assign output_data = output_sum;
endmodule
"""
    return code





verilog_code= generate_verilog_code(sin.N, sin.int_Win, sin.state_int,sin.a_scaled, sin.b_scaled,sin.c_scaled,sin.d_scaled, sin.int_Wr, sin.Wout_quantized)
with open("ESN_Generator_180.v", "w") as verilog_file:
    verilog_file.write(verilog_code)
