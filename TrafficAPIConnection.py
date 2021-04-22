import requests

#loads api key from external text file
f = open("./AzureSubscriptionKey.txt", "r")
subscriptionKey = f.read()
f.close()

print(subscriptionKey)

#example usage:
#print(GetSpeedLimit("-37.799454954912115,145.14715608507657"))
def GetSpeedLimit(CoordinatesString):
    if CoordinatesString != "-0.0,-0.0":
        api_url = "https://atlas.microsoft.com/search/address/reverse/json?subscription-key=" + subscriptionKey + "&api-version=1.0&query=" + CoordinatesString + "&returnSpeedLimit=true"
        
        try:
            response = requests.get(api_url)
        finally:
            map_json_data = response.json()

            if response.status_code == 200:
                try:
                    speedLimit = float(map_json_data["addresses"][0]["address"]["speedLimit"].replace("KPH", ""))
                finally:
                    return speedLimit
            else:
                print("api request failed!")

