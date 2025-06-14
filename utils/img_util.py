import requests
from io import BytesIO
import struct



def get_image_dimensions_from_url(url, timeout=2):
    """
    Attempts to get image dimensions without downloading the entire image.
    Returns dict with width and height or None if unable to determine.
    """
    if not url:
        return None
    
    try:
        # First try to get just enough bytes to read the header
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Read first 24 bytes which should be enough for most image headers
        chunk = response.raw.read(24)
        response.close()
        
        # Try to determine image type and dimensions
        dimensions = get_dimensions_from_bytes(chunk, url)
        if dimensions:
            return {"width": dimensions[0], "height": dimensions[1]}
            
        # If that didn't work, try downloading more bytes (up to 1KB)
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        chunk = response.raw.read(1024)
        response.close()
        
        dimensions = get_dimensions_from_bytes(chunk, url)
        if dimensions:
            return {"width": dimensions[0], "height": dimensions[1]}
            
    except Exception as e:
        print(f"Error getting image dimensions from {url}: {e}")
    
    return None


def get_dimensions_from_bytes(data, url=None):
    """
    Extract dimensions from image header bytes.
    Returns (width, height) tuple or None.
    """
    size = len(data)
    
    # PNG
    if size >= 24 and data.startswith(b'\x89PNG\r\n\x1a\n'):
        try:
            w, h = struct.unpack('>LL', data[16:24])
            return w, h
        except:
            pass
    
    # JPEG
    elif size >= 2 and data.startswith(b'\xff\xd8'):
        try:
            # JPEG is more complex, try simple SOF0 marker
            jpeg_data = BytesIO(data)
            jpeg_data.read(2)  # Skip SOI marker
            
            while True:
                marker, = struct.unpack('>H', jpeg_data.read(2))
                if marker == 0xffc0:  # SOF0 marker
                    jpeg_data.read(3)  # Skip length and precision
                    h, w = struct.unpack('>HH', jpeg_data.read(4))
                    return w, h
                else:
                    length, = struct.unpack('>H', jpeg_data.read(2))
                    jpeg_data.read(length - 2)
        except:
            pass
    
    # GIF
    elif size >= 10 and data.startswith(b'GIF'):
        try:
            w, h = struct.unpack('<HH', data[6:10])
            return w, h
        except:
            pass
    
    # WebP
    elif size >= 30 and data[8:12] == b'WEBP':
        try:
            if data[12:16] == b'VP8 ':
                w, h = struct.unpack('<HH', data[26:30])
                return w, h
        except:
            pass
    
    return None


def get_image_dimensions_safe(url, timeout=1):
    """
    Safe wrapper that returns None instead of raising exceptions.
    Useful for optional dimension fetching.
    """
    try:
        return get_image_dimensions_from_url(url, timeout)
    except:
        return None