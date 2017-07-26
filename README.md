# UberHelperBot

This is a Telegram bot that checks Uber price for the specified route and notifies either every minute or when the price drops.
Then the user can use a deep link to open Uber app and request a ride.

# Table of Contents
1. Example
2. Working with the code on your own

### Example

First meeting with the bot
![1](https://user-images.githubusercontent.com/24657053/28624307-6db0ca90-7221-11e7-8e28-e58a6f61ca23.png)

You can send the bot the start point or authorize in Uber for precise fare
![2](https://user-images.githubusercontent.com/24657053/28624342-89a7b92a-7221-11e7-9a3c-79d31b1be29c.png)

If you press /auth the inline keyboard appears and you should go to the provided link
![3](https://user-images.githubusercontent.com/24657053/28624429-c7eb4616-7221-11e7-9503-02540efe27c3.png)

Open the link for authorization
![4](https://user-images.githubusercontent.com/24657053/28624441-d1b56c94-7221-11e7-9bda-aa4498cf2f56.png)

If authorization was successful, you'll see OK
![5](https://user-images.githubusercontent.com/24657053/28624459-dc949108-7221-11e7-83dd-327261073f3d.png)

Then go back to Telegram and press the second button, that you're done. You'll see that authorization was successful.
![6](https://user-images.githubusercontent.com/24657053/28624472-e2bddbca-7221-11e7-921e-11918a6537c7.png)

Then you can send your current location as the start point
![7](https://user-images.githubusercontent.com/24657053/28624486-ee3ace90-7221-11e7-9569-d8b4dcc187b9.png)

Now send geolocation of the place you want to go
![8](https://user-images.githubusercontent.com/24657053/28624493-f55e1704-7221-11e7-8524-4a5435f92814.png)

Here you see the price and you can decide: go, wait for a cheaper fare or get notifications every minute
![9](https://user-images.githubusercontent.com/24657053/28624508-00c89c90-7222-11e7-8e94-240f51740345.png)

I decided to wait for a cheaper fare and the bot will tell me when the fare is smaller or I can send /stop if I am no longer interested
![10](https://user-images.githubusercontent.com/24657053/28624520-09f69970-7222-11e7-8cb4-13db174f538c.png)

So I got it cheaper! But I want it to be even cheaper!
![11](https://user-images.githubusercontent.com/24657053/28624530-119402a8-7222-11e7-8509-46faea5c3877.png)

The bot again will tell me when the fare will be smaller
![12](https://user-images.githubusercontent.com/24657053/28624548-1b218aa2-7222-11e7-9165-21eff0824336.png)

Yes! It's smaller again and now I want to go.
![13](https://user-images.githubusercontent.com/24657053/28624555-22dddb7e-7222-11e7-821e-c4a2ac56bd1e.png)

I press "Ok, go" and deep link to Uber app opens, I press "Open"
![14](https://user-images.githubusercontent.com/24657053/28624570-2afd9ef2-7222-11e7-996a-20a4ec3ab9ea.png)

I am in the Uber app and I only need to press "REQUEST UBERX" to request a ride
![15](https://user-images.githubusercontent.com/24657053/28624584-347d5058-7222-11e7-9f60-2a5f3eb25e1a.png)

If you want to start over, just send /start again
![16](https://user-images.githubusercontent.com/24657053/28624592-3b333d4a-7222-11e7-96b6-5e12b54a5965.png)



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