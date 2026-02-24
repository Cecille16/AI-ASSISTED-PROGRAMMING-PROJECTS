def generate_staad_warehouse():
    """
    Generate STAAD Pro input file for a 3-storey warehouse
    """
    
    # Warehouse dimensions
    length = 30.0  # meters
    width = 20.0   # meters
    height_per_floor = 4.0  # meters
    num_bays_x = 5  # along length
    num_bays_y = 4  # along width
    
    # Calculate bay spacing
    bay_x = length / num_bays_x
    bay_y = width / num_bays_y
    
    staad_input = """STAAD PLANE
START JOB INFORMATION
ENGINEER DATE 01-Jan-24
END JOB INFORMATION

INPUT
UNIT METER KN
JOINT COORDINATES
"""
    
    # Generate joint coordinates
    joint_num = 1
    joint_dict = {}
    
    for floor in range(4):  # 0 = ground, 1-3 = floors
        z = floor * height_per_floor
        for j in range(num_bays_y + 1):
            y = j * bay_y
            for i in range(num_bays_x + 1):
                x = i * bay_x
                staad_input += f"{joint_num} {x:.2f} {y:.2f} {z:.2f}\n"
                joint_dict[(i, j, floor)] = joint_num
                joint_num += 1
    
    # Member connectivity
    staad_input += "\nMEMBER INCIDENCES\n"
    
    member_num = 1
    
    # Columns (vertical members)
    staad_input += "; Columns\n"
    for floor in range(3):  # 3 storeys
        for j in range(num_bays_y + 1):
            for i in range(num_bays_x + 1):
                joint1 = joint_dict[(i, j, floor)]
                joint2 = joint_dict[(i, j, floor + 1)]
                staad_input += f"{member_num} {joint1} {joint2}\n"
                member_num += 1
    
    # Beams in X-direction
    staad_input += "; Beams X-direction\n"
    for floor in range(1, 4):  # floors 1-3
        for j in range(num_bays_y + 1):
            for i in range(num_bays_x):
                joint1 = joint_dict[(i, j, floor)]
                joint2 = joint_dict[(i + 1, j, floor)]
                staad_input += f"{member_num} {joint1} {joint2}\n"
                member_num += 1
    
    # Beams in Y-direction
    staad_input += "; Beams Y-direction\n"
    for floor in range(1, 4):  # floors 1-3
        for j in range(num_bays_y):
            for i in range(num_bays_x + 1):
                joint1 = joint_dict[(i, j, floor)]
                joint2 = joint_dict[(i, j + 1, floor)]
                staad_input += f"{member_num} {joint1} {joint2}\n"
                member_num += 1
    
    # Bracing (X-bracing in some bays)
    staad_input += "; Bracing\n"
    for floor in range(3):  # between floors
        # Add bracing in end bays
        for bay_x_pos in [0, num_bays_x - 1]:
            for bay_y_pos in range(num_bays_y):
                # Diagonal 1
                joint1 = joint_dict[(bay_x_pos, bay_y_pos, floor)]
                joint2 = joint_dict[(bay_x_pos + 1, bay_y_pos + 1, floor + 1)]
                staad_input += f"{member_num} {joint1} {joint2}\n"
                member_num += 1
                
                # Diagonal 2
                joint1 = joint_dict[(bay_x_pos + 1, bay_y_pos, floor)]
                joint2 = joint_dict[(bay_x_pos, bay_y_pos + 1, floor + 1)]
                staad_input += f"{member_num} {joint1} {joint2}\n"
                member_num += 1
    
    # Define member properties
    staad_input += """
DEFINE MATERIAL START
ISOTROPIC STEEL
E 200000000
POISSON 0.3
DENSITY 78.5
ALPHA 1.2e-005
DAMP 0.03
END DEFINE MATERIAL

MEMBER PROPERTY
"""
    
    # Assign properties to different member types
    total_columns = (num_bays_x + 1) * (num_bays_y + 1) * 3
    total_beams_x = (num_bays_x) * (num_bays_y + 1) * 3
    total_beams_y = (num_bays_x + 1) * (num_bays_y) * 3
    
    # Column properties
    staad_input += f"1 TO {total_columns} PRIS YD 0.4 ZD 0.4\n"
    
    # Beam X properties
    beam_x_start = total_columns + 1
    beam_x_end = total_columns + total_beams_x
    staad_input += f"{beam_x_start} TO {beam_x_end} PRIS YD 0.5 ZD 0.3\n"
    
    # Beam Y properties
    beam_y_start = beam_x_end + 1
    beam_y_end = beam_x_end + total_beams_y
    staad_input += f"{beam_y_start} TO {beam_y_end} PRIS YD 0.5 ZD 0.3\n"
    
    # Bracing properties
    bracing_start = beam_y_end + 1
    staad_input += f"{bracing_start} TO {member_num - 1} PRIS YD 0.15 ZD 0.15\n"
    
    # Constants and supports
    staad_input += """
CONSTANTS
MATERIAL STEEL ALL

SUPPORTS
"""
    
    # Fixed supports at base
    for j in range(num_bays_y + 1):
        for i in range(num_bays_x + 1):
            joint_base = joint_dict[(i, j, 0)]
            staad_input += f"{joint_base} FIXED\n"
    
    # Loading
    staad_input += """
LOADING 1 Dead Load
MEMBER LOAD
; Dead load on beams (self weight + slab)
"""
    
    # Apply dead loads
    for floor in range(1, 4):
        staad_input += f"; Floor {floor}\n"
        # Dead load on beams (including slab weight)
        beam_start_x = total_columns + (floor - 1) * (total_beams_x // 3) + 1
        beam_end_x = total_columns + floor * (total_beams_x // 3)
        staad_input += f"{beam_start_x} TO {beam_end_x} UNI GY -15\n"
        
        beam_start_y = beam_x_end + (floor - 1) * (total_beams_y // 3) + 1
        beam_end_y = beam_x_end + floor * (total_beams_y // 3)
        staad_input += f"{beam_start_y} TO {beam_end_y} UNI GY -15\n"
    
    staad_input += """
LOADING 2 Live Load
MEMBER LOAD
; Live load on beams
"""
    
    # Apply live loads
    for floor in range(1, 4):
        staad_input += f"; Floor {floor}\n"
        beam_start_x = total_columns + (floor - 1) * (total_beams_x // 3) + 1
        beam_end_x = total_columns + floor * (total_beams_x // 3)
        staad_input += f"{beam_start_x} TO {beam_end_x} UNI GY -5\n"
        
        beam_start_y = beam_x_end + (floor - 1) * (total_beams_y // 3) + 1
        beam_end_y = beam_x_end + floor * (total_beams_y // 3)
        staad_input += f"{beam_start_y} TO {beam_end_y} UNI GY -5\n"
    
    staad_input += """
LOADING 3 Wind Load X
JOINT LOAD
; Wind load in X direction on exposed joints
"""
    
    # Wind load (simplified)
    for floor in range(1, 4):
        wind_pressure = 1.5 * floor  # Increasing with height
        for j in [0, num_bays_y]:  # End faces
            for i in range(num_bays_x + 1):
                joint_wind = joint_dict[(i, j, floor)]
                staad_input += f"{joint_wind} FX {wind_pressure}\n"
    
    staad_input += """
LOAD COMBINATION 4 1.2 DL + 1.6 LL
1 1.2 2 1.6

LOAD COMBINATION 5 1.2 DL + 1.6 WL
1 1.2 3 1.6

PERFORM ANALYSIS

PRINT SUPPORT REACTIONS
PRINT MEMBER FORCES ALL
PRINT MEMBER STRESSES ALL
PRINT DISPLACEMENTS ALL

FINISH
"""
    
    return staad_input


def save_staad_file(filename="warehouse_3storey.std"):
    """
    Generate and save STAAD input file
    """
    staad_code = generate_staad_warehouse()
    
    with open(filename, 'w') as file:
        file.write(staad_code)
    
    print(f"STAAD file '{filename}' generated successfully!")
    print("\nFile includes:")
    print("- 3-storey warehouse structure")
    print("- 30m x 20m plan dimensions")
    print("- 4m floor height")
    print("- Columns, beams, and bracing")
    print("- Dead, live, and wind loading")
    print("- Load combinations")
    print("- Analysis commands")
    
    return staad_code


# Additional utility functions
def modify_warehouse_dimensions(length, width, height_per_floor, num_bays_x, num_bays_y):
    """
    Modify warehouse dimensions - you can customize this function
    """
    # This is a template for customizing dimensions
    # You would modify the generate_staad_warehouse function with these parameters
    pass


def add_crane_beam(crane_capacity=10):
    """
    Function to add crane beam loading (for future enhancement)
    """
    # Template for adding crane beam considerations
    print(f"Crane beam design for {crane_capacity} ton capacity would be added here")
    pass


# Generate the STAAD file
if __name__ == "__main__":
    # Generate and save the file
    staad_content = save_staad_file()
    
    # Optionally print first few lines to verify
    print("\nFirst 20 lines of generated file:")
    print("-" * 50)
    lines = staad_content.split('\n')
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:2d}: {line}")
