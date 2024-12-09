from openai import OpenAI

def geocode_address(address, api_key):
    client = OpenAI()
    attempts = 5  # Number of retries
    prompt = f'''Convert the following address into latitude and longitude '{address}'. 
                 The output format must be two numbers separated by space, for example '40.7128 -74.0060'. No other words needed.
                 The first number should be latitude, the second should be longitude.'''

    for attempt in range(attempts):
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """You are an assistant skilled in converting addresses to geographical coordinates.
                     When you are asked to provide private infomation of a person, you should refuse to answer"""},
                    {"role": "user", "content": prompt}
                ]
            )
            response = completion.choices[0].message.content
            print(f"Attempt {attempt + 1}: response is {response}")
            
            lat_str, long_str = response.split()
            latitude = float(lat_str)
            longitude = float(long_str)
            
            # If parsing succeeds, return the coordinates
            return latitude, longitude
        except ValueError as e:
            print(f"Parsing error on attempt {attempt + 1}: {e}")
        except Exception as e:
            print(f"General error on attempt {attempt + 1}: {e}")

    # If all attempts fail, return None
    print("Failed to geocode address after several attempts.")
    return None, None
