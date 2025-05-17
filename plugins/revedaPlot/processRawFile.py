import numpy as np
from collections import namedtuple

columnTag = namedtuple('columnTag',['order','name', 'type'])


class RawDataFileReader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.header_lines = []
        self.binary_data = b""
        self._read_file()

    def _read_file(self):
        with open(self.filepath, "rb") as f:
            header_bytes = []
            while True:
                line = f.readline()
                if not line:
                    break  # End of file
                header_bytes.append(line)
                if line.strip() == b"Binary:":
                    break
            self.header_lines = [l.decode("utf-8", errors="replace").rstrip("\r\n") for l in header_bytes]
            self.binary_data = f.read()  # The rest is binary

    def get_header(self):
        """Return the header as a list of lines (strings)."""
        return self.header_lines

    def get_header_str(self):
        """Return the header as a single string."""
        return "\n".join(self.header_lines)

    def get_binary_data(self):
        """Return the binary data as bytes."""
        return self.binary_data

    def get_header_dict(self):
        """Parse the header lines into a dictionary."""
        header_dict = {}
        variables = []
        in_variables_section = False

        for line in self.header_lines:
            if line.strip() == "Variables:":
                in_variables_section = True
                continue
            if in_variables_section and line.strip() and not line.startswith("\t"):
                in_variables_section = False
            if in_variables_section and line.strip():
                parts = line.strip().split()
                if len(parts) >= 3:
                    variables.append(columnTag(int(parts[0]), parts[1], parts[2]))
            if ":" in line and not in_variables_section:
                key, value = line.split(":", 1)
                header_dict[key.strip()] = value.strip()

        if variables:
            header_dict["Variables"] = variables
        return header_dict

    def get_data_array(self):
        """Parse the binary data into a structured numpy array with named columns."""
        header_dict = self.get_header_dict()
        plotname = header_dict.get("Plotname", "")
        num_variables = int(header_dict.get("No. Variables", 0))
        num_points = int(header_dict.get("No. Points", 0))

        if not num_variables or not num_points:
            return None

        variables = header_dict.get("Variables", [])
        if not variables:
            return None

        # Extract column names from variables
        column_names = [var.name for var in variables]

        if "AC" in plotname:
            # Complex data: each point is 2 doubles
            dtype = np.dtype([(name, np.complex128) for name in column_names])
            data = np.frombuffer(self.binary_data, dtype=np.float64).reshape(num_points, num_variables * 2)
            data = data.view(np.complex128).reshape(num_points, num_variables)
        else:
            # Real data: each point is 1 double
            dtype = np.dtype([(name, np.float64) for name in column_names])
            data = np.frombuffer(self.binary_data, dtype=np.float64).reshape(num_points, num_variables)

        # Convert to structured array
        structured_data = np.zeros(num_points, dtype=dtype)
        for i, name in enumerate(column_names):
            structured_data[name] = data[:, i]

        return structured_data


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python raw_data_reader.py <filepath>")
        sys.exit(1)
    filepath = sys.argv[1]
    reader = RawDataFileReader(filepath)
    print("Header:")
    print(reader.get_header_str())
    print("\nHeader Dictionary:")
    print(reader.get_header_dict())
    print("\nBinary data size:", len(reader.get_binary_data()), "bytes")
    data = reader.get_data_array()
    if data is not None:
        print("\nData array shape:", data.shape)
        print("Data array dtype:", data.dtype)
        print("First few data points:")

        print(data.dtype.names[0]) 