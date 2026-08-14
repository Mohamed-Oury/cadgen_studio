import sys
import ezdxf

def inspect_dxf(filepath):
    try:
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        
        layers = {}
        for entity in msp:
            layer_name = entity.dxf.layer
            layers[layer_name] = layers.get(layer_name, 0) + 1
            
        print("Layer statistics:")
        for layer, count in sorted(layers.items()):
            print(f" - {layer}: {count} entities")
            
    except Exception as e:
        print(f"Error reading DXF: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_dxf(sys.argv[1])
    else:
        print("Please provide a DXF file path.")
