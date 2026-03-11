#!/bin/bash

# Parse command line arguments
SEARCH_DIR="${1:-.}"  # Use first argument or current directory as default

OUTPUT_DIR_NAME="renders"
ZOOM=0.7
WIDTH=1080
HEIGHT=1080
ROTATE_X=0
ROTATE_Z=-45
ROTATION=360 # Total rotation angle
STEP=3 # Rotation step in degrees
FRAMERATE=30 # Framerate for the final video

# Create output directory in the search directory
OUTPUT_DIR="$SEARCH_DIR/$OUTPUT_DIR_NAME/"
mkdir -p "$OUTPUT_DIR"

# Find all .kicad_pcb files in the specified directory
KICAD_FILES=("$SEARCH_DIR"/*.kicad_pcb)

# Check if any .kicad_pcb files exist
if [ ! -e "${KICAD_FILES[0]}" ]; then
    echo "No .kicad_pcb files found in directory: $SEARCH_DIR"
    echo "Usage: $0 [directory]"
    echo "  directory: Directory to search for .kicad_pcb files (default: current directory)"
    exit 1
fi

echo "Searching in directory: $SEARCH_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Found ${#KICAD_FILES[@]} KiCad PCB file(s) to process:"
for file in "${KICAD_FILES[@]}"; do
    echo "  - $file"
done
echo

# Process each .kicad_pcb file
for INPUT_FILE in "${KICAD_FILES[@]}"; do
    echo "Processing $INPUT_FILE..."
    
    # Create a temporary directory for this file
    TEMP_DIR=$(mktemp -d)
    
    # Make sure the temp directory gets cleaned up when processing this file is done
    trap 'rm -rf "$TEMP_DIR"' EXIT
    
    # Extract base name for output file
    BASE_NAME=$(basename "$INPUT_FILE" .kicad_pcb)
    OUTPUT_VIDEO="${OUTPUT_DIR}${BASE_NAME}.mp4"
    
    echo "Rendering $((ROTATION/STEP)) frames for $INPUT_FILE..."
    
    let FRAMES=ROTATION/STEP
    for ((i = 0; i < FRAMES; i++)); do
        ROTATE_Y=-$(($i * STEP))
        OUTPUT_PATH="$TEMP_DIR/frame$i.png"
        echo "  Rendering frame $i ($ROTATE_Y degrees)"
        kicad-cli pcb render --rotate "$ROTATE_X,$ROTATE_Y,$ROTATE_Z" --zoom $ZOOM -w $WIDTH -h $HEIGHT --background opaque --quality high --light-side .15 --light-side-elevation 135 -o "$OUTPUT_PATH" "$INPUT_FILE" > /dev/null || { echo "Error rendering frame $i. Exiting."; exit 1; }
    done

    # Combine frames into an iPhone-compatible MP4
    # -c:v libx264: H.264 codec
    # -pix_fmt yuv420p: Required for most players/iPhone
    # -profile:v high -level 4.1: Standard compatibility
    # -crf 18: High quality (lower is better, 18-23 is standard)
    # -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2": Ensures dimensions are even (required for yuv420p)
    ffmpeg -y -framerate $FRAMERATE -i "$TEMP_DIR/frame%d.png" -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.1 -crf 18 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" "$OUTPUT_VIDEO" > /dev/null 2>&1

    echo "✓ Video created: $OUTPUT_VIDEO"
    
    # Clean up temp directory for this file
    rm -rf "$TEMP_DIR"
done

echo "All videos created successfully!"
