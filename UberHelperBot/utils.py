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
def estimate_price(start_lat, start_long, end_lat, end_long):
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

