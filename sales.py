import requests
import json
import time
from datetime import datetime

class openseaSalesBot():
    def __init__(self):
        self.asset_range = 1
        self.collection_slug = input("Collection Slug: ")

    def requestLastSales(self):
        # Request event data
        json_data = self.successfulEventData()
        return self.parseSuccesfulEventData(json_data)

    def successfulEventData(self):
        url = "https://api.opensea.io/api/v1/events"
        querystring = {"only_opensea": "true", "offset": "0", "limit": str(self.asset_range),
                       "collection_slug": self.collection_slug, "event_type": "successful"}
        response = requests.request("GET", url, headers={"Accept": "application/json"}, params=querystring)
        return json.loads(response.text)

    def parseSuccesfulEventData(self, json_dump):
        json_list = []
        # Loop through the last sales
        for i in range(self.asset_range):
            # json only contains the last sale info
            asset_info = json_dump['asset_events'][i]['asset']
            image_url = asset_info['image_url']
            punk_name = asset_info['name']
            token_id = asset_info['token_id']
            product_link = asset_info['permalink']

            # Seller info
            seller_info = json_dump['asset_events'][i]['seller']
            if (seller_info['user'] == None):
                seller_username = 'None'
            else:
                seller_username = seller_info['user']['username']
            seller_address = seller_info['address']

            # Buyer info
            buyer_info = json_dump['asset_events'][i]['winner_account']
            if (buyer_info['user'] == None):
                buyer_username = 'None'
            else:
                buyer_username = buyer_info['user']['username']
            buyer_address = buyer_info['address']

            payment_info = json_dump['asset_events'][i]['payment_token']
            payment_token = payment_info['symbol']

            sale_id = json_dump['asset_events'][i]['id']
            sale_price = int(json_dump['asset_events'][i]['total_price']) / 1000000000000000000
           

            json_info = {
                'asset_info': {
                    'asset_name': punk_name,
                    'asset_image': image_url,
                    'asset_link': product_link,
                    'token_id': token_id,
                },
                'seller_info': {
                    'seller_username': seller_username,
                    'seller_address': seller_address
                },
                'buyer_info': {
                    'buyer_username': buyer_username,
                    'buyer_address': buyer_address
                },
                'payment_token': payment_token,
                'sale_price': sale_price,
                'sale_id': sale_id,

            }
            json_list.append(json_info)
        return json_list

    def sendWebhook(self, sale_json):
        discord_webhook = 'WEBHOOK'

        asset_info = sale_json['asset_info']
        seller_info = sale_json['seller_info']
        buyer_info = sale_json['buyer_info']
        payment_token = sale_json['payment_token']
        sale_price = sale_json['sale_price']

        json_info = json.dumps(
            {
                'embeds': [
                    {
                        'title': f"#{asset_info['token_id']} was purchased!",
                        'url': asset_info['asset_link'],
                        'fields': [
                            {
                                'name': '**Sale price**',
                                'value': f'{sale_price} {payment_token}',
                                'inline': 'false'
                            },
                            {
                                'name': '**Buyer**',
                                'value': f"[{buyer_info['buyer_username']}](https://opensea.io/{buyer_info['buyer_address']})",
                                'inline': 'true'
                            },
                            {
                                'name': '**Seller**',
                                'value': f"[{seller_info['seller_username']}](https://opensea.io/{seller_info['seller_address']})",
                                'inline': 'true'
                            }
                        ],
                        'image': {
                            'url': asset_info['asset_image']
                        },
                        'footer': {
                            'text': f'PROJECT NAME',  # Change this to your projects name or set as variable
                            'icon_url': 'PROJECT LOGO'
                            # Change this to your projects logo
                        }
                    }
                ]
            }
        )
        requests.post(discord_webhook, data=json_info, headers={"Content-Type": "application/json"})
        #Print for debugging/local env use
        print(f'Sale Info: {json_info}')

    def runInstance(self):
        old_sale_list = self.requestLastSales()
        old_sale_id = []

        for i in range(self.asset_range):
            old_sale_id.append(old_sale_list[i]['sale_id'])

        while (True):
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            new_sales = []

            try:
                new_sales_list = self.requestLastSales()
                new_sale_id = []

                for i in range(self.asset_range):
                    new_sale_id.append(new_sales_list[i]['sale_id'])

            except Exception as e:
                new_sales_list = old_sale_list
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print(f'[{current_time}] Error - {e}')

            new_sales = list(set(new_sale_id) - set(old_sale_id))

            if new_sales != []:

                for i in range(len(new_sales)):
                    print(f"[{current_time}] New  sale! - {new_sales[i]}")

                    for j in range(len(new_sales_list)):
                        if new_sales_list[j]['sale_id'] == new_sales[i]:

                            # Data for tweet
                            asset_name = new_sales_list[j]['asset_info']['asset_name']
                            asset_link = new_sales_list[j]['asset_info']['asset_link']
                            sale_price = new_sales_list[j]['sale_price']
                            payment_token = new_sales_list[j]['payment_token']

                            sale_data = [asset_name, asset_link, sale_price, payment_token]

                            try:
                                self.sendWebhook(new_sales_list[j])
                                print(f'Sale Short: {sale_data}')
                            except Exception as e:
                                print(f'Error: {e}')

            else:
                print(f'[{current_time}] No new sales!')

            old_sale_id = new_sale_id
            old_sale_list = new_sales_list

            time.sleep(30)  # Delay for requesting the opensea api

            # TEST

bot = openseaSalesBot()
bot.runInstance()