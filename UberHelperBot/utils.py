import api_keys as keys


# generate deep link
def make_deep_link(start_latitude, start_longitude, end_latitude, end_longitude):
    deep_link = 'https://m.uber.com/ul/?action=setPickup&client_id={client_id}&pickup[formatted_address]=' \
                'start&pickup[latitude]={start_latitude}&pickup[longitude]={start_longitude}&' \
                'dropoff[formatted_address]=end&dropoff[latitude]={end_latitude}&' \
                'dropoff[longitude]={end_longitude}'.format(client_id=keys.UBER_CLIENT_ID,
                                                            start_latitude=start_latitude,
                                                            start_longitude=start_longitude,
                                                            end_latitude=end_latitude,
                                                            end_longitude=end_longitude)
    return deep_link


# approximate price from Uber
def estimate_price(client, start_lat, start_long, end_lat, end_long):
    response = client.get_price_estimates(
        start_latitude=start_lat,
        start_longitude=start_long,
        end_latitude=end_lat,
        end_longitude=end_long,
        seat_count=2
    )

    high = response.json.get('prices')[0]['high_estimate']
    # this calculation is based on experience, not always correct
    fixed = int(high + high / 100 * 13)
    return fixed


# real price from uber
def get_real_price(client, product_id, start_lat, start_long, end_lat, end_long):
    estimate = client.estimate_ride(
        product_id=product_id,
        start_latitude=start_lat,
        start_longitude=start_long,
        end_latitude=end_lat,
        end_longitude=end_long,
        seat_count=2
    )

    fare = int(estimate.json.get('fare')['value'])
    return fare


# some fun with stickers
tuple_of_stickers = ('CAADAgADoQQAAvoLtgjKyWXmCJBFiQI', 'CAADAgADswQAAvoLtgjn1HatrplOYgI',
                     'CAADAgADKQQAAvoLtggbjYlD46d10wI', 'CAADAgADLQQAAvoLtghiigzVyvC9dQI',
                     'CAADAgADgAQAAvoLtggFLHtXU9e9AAEC', 'CAADAgAD4wQAAvoLtgiihzsbgI6e3QI',
                     'CAADAgADcAQAAvoLtgjnJAvUbGUoNAI', 'CAADAgADQwQAAvoLtgjxCQ-qMZR60gI',
                     'CAADAgAEBQAC-gu2CHQAARtDOddWpwI', 'CAADAgADDAUAAvoLtghHvNZAN0CAmgI',
                     'CAADAgADZwUAAvoLtggOeXkq3Q_pUgI', 'CAADAgADGAUAAvoLtghZrHo-l3Wx3QI',
                     'CAADAgADYQUAAvoLtghuKtlqKBkFHgI', 'CAADAgADYwUAAvoLtghplScAAVcXU7wC',
                     'CAADAgADagUAAvoLtghD9cxUspWcUgI', 'CAADAgADaQUAAvoLtgj4-nsRDiR2kwI',
                     'CAADAgADHAUAAvoLtghbYeD4O-0D1gI', 'CAADAgADGgUAAvoLtghprPpBQxlMrAI',
                     'CAADAgADxQQAAvoLtght1d8Kw5fIOwI', 'CAADAgADUAQAAvoLtgjxcf3WGo1vcQI',
                     'CAADAgADdAQAAvoLtggUqm04r4Au9wI', 'CAADAgADwwQAAvoLtgiyQa_zvBHWHwI',
                     'CAADAgADagQAAvoLtgjq_-LDppFBPwI', 'CAADAgADdgQAAvoLtggkbYpQlP7OuAI',
                     'CAADAgADeAQAAvoLtgh9GkGIlCa-HwI', 'CAADAgADlQQAAvoLtgiJOGpG-9l3DwI',
                     'CAADAgADmQQAAvoLtghV1qTg8UrG1gI', 'CAADAgADrQQAAvoLtgiyhUZm6S9pEQI',
                     'CAADAgADfAQAAvoLtgiEKs3s50ngHAI', 'CAADAgADpwQAAvoLtgjV0bycBrY_dgI')