# UberHelperBot

This is a Telegram bot that checks Uber price for the specified route and notifies either every minute or when the price drops.
Then the user can use a deep link to open Uber app and request a ride.

# Table of Contents
1. Example
2. Working with the code on your own

### Example

First meeting with the bot

![1](https://user-images.githubusercontent.com/24657053/28628032-26d503f6-722c-11e7-89fe-75658fcd2d71.png)

You can send the bot the start point or authorize in Uber for precise fare

![2](https://user-images.githubusercontent.com/24657053/28628037-26da3e7a-722c-11e7-8d8f-001b3ba75509.png)

If you press /auth the inline keyboard appears and you should go to the provided link

![3](https://user-images.githubusercontent.com/24657053/28628033-26d57818-722c-11e7-8906-c7a27fa1f03c.png)

Open the link for authorization

![4](https://user-images.githubusercontent.com/24657053/28628034-26d5a4a0-722c-11e7-82eb-ebf0703756d2.png)

If authorization was successful, you'll see OK

![5](https://user-images.githubusercontent.com/24657053/28628036-26d75aac-722c-11e7-996f-5d38ab43df96.png)

Then go back to Telegram and press the second button, that you're done. You'll see that authorization was successful.

![6](https://user-images.githubusercontent.com/24657053/28628035-26d71e98-722c-11e7-9ce8-98a7d7710cd7.png)

Then you can send your current location as the start point

![7](https://user-images.githubusercontent.com/24657053/28628040-26f4ab7a-722c-11e7-9f31-32b6c1db22e2.png)

Now send geolocation of the place you want to go

![8](https://user-images.githubusercontent.com/24657053/28628039-26ef3424-722c-11e7-84d8-1631716b0c60.png)

Here you see the price and you can decide: go, wait for a cheaper fare or get notifications every minute

![9](https://user-images.githubusercontent.com/24657053/28628038-26eed24a-722c-11e7-9798-711a94e1022d.png)

I decided to wait for a cheaper fare and the bot will tell me when the fare is smaller or I can send /stop if I am no longer interested

![10](https://user-images.githubusercontent.com/24657053/28628042-26f72a6c-722c-11e7-8e96-e4f8e6823da7.png)

So I got it cheaper! But I want it to be even cheaper!

![11](https://user-images.githubusercontent.com/24657053/28628043-26f97eb6-722c-11e7-9ef2-b71bba652d19.png)

The bot again will tell me when the fare will be smaller

![12](https://user-images.githubusercontent.com/24657053/28628041-26f69e9e-722c-11e7-8966-5be3ea27f6ed.png)

Yes! It's smaller again and now I want to go.

![13](https://user-images.githubusercontent.com/24657053/28628044-270867be-722c-11e7-8f43-c18573f72ea5.png)

I press "Ok, go" and deep link to Uber app opens, I press "Open"

![14](https://user-images.githubusercontent.com/24657053/28628045-270a96ce-722c-11e7-8a19-7e0bcb748107.png)

I am in the Uber app and I only need to press "REQUEST UBERX" to request a ride

![15](https://user-images.githubusercontent.com/24657053/28628046-2710d0ca-722c-11e7-94aa-8733ae174f71.png)

If you want to start over, just send /start again

![16](https://user-images.githubusercontent.com/24657053/28628047-2718276c-722c-11e7-9609-3bf323a1a272.png)



### Working with the code on your own
---------------------------------
1. register your app in [Uber](https://developer.uber.com/)
2. register a telegram bot – talk to @BotFather
3. clone the repository
4. create api_keys.py in innermost directory

```python
UBER_CLIENT_ID = # your Client ID from Uber
UBER_SERVER_TOKEN = # your Server Token from Uber
UBER_CLIENT_SECRET = # your Client Secret from Uber
UBER_REDIRECT_URL = # your Redirect URL as specified in Uber (can be '127.0.0.1')
TELEGRAM_TOKEN = # your Telegram Token from @BotFather
DB_ADDRESS = # location of the database, e.g. 'sqlite:///user_rides.sqlite' (absolute path is strongly recommended!)
```

5. install requirements
```python
pip install -r requirements.txt
```

6. run models.py to create a database
```python
python models.py
```

7. run server.py to catch redirected links from Uber
```python
python server.py
```

8. open another terminal window and run the bot
```python
python UberHelperBot.py
```

9. find the bot by the name you have registered in step 2 and talk to it.

10. it should work :)