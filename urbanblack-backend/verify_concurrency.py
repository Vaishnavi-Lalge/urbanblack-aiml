import requests
import concurrent.futures
import time
import random

# Configuration
BASE_URL = "http://localhost:8089/api/v1/node/create"
NUM_NODES = 50
CONCURRENT_THREADS = 10

def create_node(user_id):
    headers = {
        "X-User-Id": str(user_id)
    }
    try:
        response = requests.post(BASE_URL, headers=headers, timeout=5)
        return response.status_code, response.text
    except Exception as e:
        return 0, str(e)

def run_test():
    print(f"🚀 Starting Concurrency Test: {NUM_NODES} nodes with {CONCURRENT_THREADS} threads...")
    start_time = time.time()
    
    # Simulating 50 different users
    user_ids = list(range(1001, 1001 + NUM_NODES))
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREADS) as executor:
        future_to_user = {executor.submit(create_node, uid): uid for uid in user_ids}
        for future in concurrent.futures.as_completed(future_to_user):
            results.append(future.result())

    end_time = time.time()
    total_time = end_time - start_time
    
    # Summary
    success_count = sum(1 for status, _ in results if status == 200)
    error_count = NUM_NODES - success_count
    
    print("\n" + "="*40)
    print(f"📊 Test Results Summary:")
    print(f"Total Requests: {NUM_NODES}")
    print(f"Successful:     {success_count}")
    print(f"Failed:         {error_count}")
    print(f"Total Time:     {total_time:.2f} seconds")
    print(f"Avg Speed:      {NUM_NODES/total_time:.2f} nodes/sec")
    print("="*40)

    if error_count > 0:
        print("\n❌ Sample Errors:")
        for status, text in results:
            if status != 200:
                print(f"Status {status}: {text[:100]}")
    else:
        print("\n✅ All nodes inserted successfully!")
        print("Now verify the tree structure and wallet balances in the database.")

if __name__ == "__main__":
    run_test()
