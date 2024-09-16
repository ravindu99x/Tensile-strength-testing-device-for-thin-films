import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import csv

# Use a larger font size for buttons
button_font = ('Helvetica', 14)


# Function to list available COM ports
def list_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


# Global variable for serial connection
ser = None

# Lists to store sensor data
sensorValue1_data = []
sensorValue2_data = []

# Set up the GUI
root = tk.Tk()
root.title("Tensile_test_EPL_Mini_project_s14832")

# Dropdown menu for COM port selection
com_port_var = tk.StringVar(root)
com_ports = list_com_ports()
com_port_var.set(com_ports[0] if com_ports else "")
com_port_dropdown = ttk.Combobox(root, textvariable=com_port_var, values=com_ports, state="readonly")
com_port_dropdown.pack(side=tk.TOP, fill=tk.X)


# Function to update the COM port dropdown
def update_com_ports():
    com_ports = list_com_ports()
    com_port_var.set(com_ports[0] if com_ports else "")
    com_port_dropdown['values'] = com_ports


# Function to connect to the selected COM port
def connect_to_com_port():
    global ser
    selected_port = com_port_var.get()
    if selected_port:
        try:
            if ser is not None:
                ser.close()  # Close existing connection if any
                ser = None   # Reset the global serial variable
            ser = serial.Serial(selected_port, 115200, timeout=1)
            start_test_button['state'] = 'normal'  # Enable the "Start Test" button
            clear_plot()  # Optionally clear the plot when connecting to a new port
            root.after(1, update_plot)  # Restart the plotting loop
        except serial.SerialException as e:
            print(f"Failed to connect on {selected_port}. Error: {e}")


# Connect button
connect_button = ttk.Button(root, text="Connect", command=connect_to_com_port, width=20, style='my.TButton')
connect_button.pack(side=tk.TOP, fill=tk.X, pady=5)

# Refresh COM ports button
refresh_button = ttk.Button(root, text="Refresh Ports", command=update_com_ports, width=20, style='my.TButton')
refresh_button.pack(side=tk.TOP, fill=tk.X, pady=5)

# Frame for plot
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# Matplotlib figure and canvas for plotting
fig = Figure()
ax = fig.add_subplot(111)
ax.set_xlabel('Strain (ε)')
ax.set_ylabel('Stress (σ)')
ax.set_title('Stress-Strain Curve')  # Setting the title
ax.grid(True)  # Turning on the grid
line, = ax.plot(sensorValue1_data, sensorValue2_data, linestyle='-')

canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)


# Function to update the plot
def update_plot():
    if ser and ser.isOpen() and ser.in_waiting:  # Check if ser is not None and the port is open
        data_line = ser.readline().decode('utf-8').strip()
        if data_line:
            try:
                sensorValues = list(map(float, data_line.split(', ')))
                if len(sensorValues) == 2:
                    sensorValue1_data.append(sensorValues[0])
                    sensorValue2_data.append(sensorValues[1])
                    line.set_xdata(sensorValue1_data)
                    line.set_ydata(sensorValue2_data)
                    ax.relim()
                    ax.autoscale_view(True,True,True)
                    canvas.draw()
            except ValueError:
                pass  # Handle error if needed
    root.after(100, update_plot)  # Adjust the update rate as needed



# Modify the start_test function
def start_test():
    if ser:
        motor_speed = motor_speed_var.get()
        sample_thickness = sample_thickness_var.get()
        # Format the command with speed and thickness
        command = f"START,{motor_speed},{sample_thickness}\n"
        ser.write(command.encode())


# Function to reset the stepper motor position
def reset_motor_position():
    if ser:
        ser.write("RESET\n".encode())


# Function to clear the plot
def clear_plot():
    sensorValue1_data.clear()
    sensorValue2_data.clear()
    ax.cla()
    ax.set_xlabel('Strain (ε)')
    ax.set_ylabel('Stress (σ)')
    ax.set_title('Stress-Strain Curve')  # Setting the title
    ax.grid(True)  # Turning on the grid
    global line
    line, = ax.plot(sensorValue1_data, sensorValue2_data, linestyle='-')
    canvas.draw()


# Function to save collected data to a CSV file
def save_data():
    with open('sensor_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Strain', 'Stress'])
        for s1, s2 in zip(sensorValue1_data, sensorValue2_data):
            writer.writerow([s1, s2])


# Function to save the plot as a PNG file
def save_plot_as_png():
    fig.savefig('stress_strain_curve.png')

# Add input fields for motor speed and sample thickness
motor_speed_var = tk.IntVar(value=1000)  # Default speed
sample_thickness_var = tk.DoubleVar(value=0.0001)  # Default thickness in mm

# Add descriptive labels and larger entry fields for motor speed and sample thickness

# Label for Motor Speed
motor_speed_label = tk.Label(root, text="Motor Speed (Value in range: 500 to 3000):")
motor_speed_label.pack(side=tk.TOP, fill=tk.X)

# Entry for Motor Speed with a larger font
motor_speed_entry = ttk.Entry(root, textvariable=motor_speed_var, font=('Helvetica', 12))
motor_speed_entry.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

# Label for Sample Thickness
sample_thickness_label = tk.Label(root, text="Sample Thickness (m):")
sample_thickness_label.pack(side=tk.TOP, fill=tk.X)

# Entry for Sample Thickness with a larger font
sample_thickness_entry = ttk.Entry(root, textvariable=sample_thickness_var, font=('Helvetica', 12))
sample_thickness_entry.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

# Adjusting other GUI elements to match the new geometry
connect_button.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))
refresh_button.pack(side=tk.TOP, fill=tk.X, pady=(2, 10))

# Ensure the frame (plot area) expands more significantly to improve visibility
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Adjusting button sizes and layout
button_frame = ttk.Frame(root)  # A frame to contain control buttons for a cleaner layout
button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

# Button to start the test
start_test_button = ttk.Button(root, text="Start Test", command=start_test, state='disabled', width=20, style='my.TButton')
start_test_button.pack(in_=button_frame, side=tk.LEFT, expand=True, padx=(5, 2))

# Reset motor position button
reset_motor_button = ttk.Button(root, text="Reset Motor Position", command=reset_motor_position, width=20, style='my.TButton')
reset_motor_button.pack(in_=button_frame, side=tk.LEFT, expand=True, padx=2)

# Button to clear the plot
clear_plot_button = ttk.Button(root, text="Clear Plot", command=clear_plot, width=20, style='my.TButton')
clear_plot_button.pack(in_=button_frame, side=tk.LEFT, expand=True, padx=2)

# Button to save data
save_data_button = ttk.Button(root, text="Save Data", command=save_data, width=20, style='my.TButton')
save_data_button.pack(in_=button_frame, side=tk.LEFT, expand=True, padx=2)

# Button to save plot as PNG
save_plot_button = ttk.Button(root, text="Save Plot", command=save_plot_as_png, width=20, style='my.TButton')
save_plot_button.pack(in_=button_frame, side=tk.LEFT, expand=True, padx=(2, 5))

# Styling the buttons
style = ttk.Style()
style.configure('my.TButton', font=button_font)

root.after(1, update_plot)  # Start the update loop for plotting
root.mainloop()
