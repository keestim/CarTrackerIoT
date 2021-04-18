import requests

f = open("./AzureSubscriptionKey.txt", "r")
subscriptionKey = f.read()
f.close()

print(subscriptionKey)

def GetSpeedLimit(CoordinatesString):
    api_url = "https://atlas.microsoft.com/search/address/reverse/json?subscription-key=" + subscriptionKey + "&api-version=1.0&query=" + CoordinatesString + "&returnSpeedLimit=true"

    response = requests.get(api_url)
    map_json_data = response.json()

    if response.status_code  == 200:
        speedLimit = float(map_json_data["addresses"][0]["address"]["speedLimit"].replace("KPH", ""))
        return speedLimit
    else:
        print("api request failed!")

#example usage:
#print(GetSpeedLimit("-37.799454954912115,145.14715608507657"))