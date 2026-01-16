# Pickup Location Feature Setup Guide

This guide explains the new pickup location feature that allows customers to choose between shipping and pickup for physical products.

## Features

✅ **Admin Panel**: Manage pickup locations (add, edit, activate/deactivate)  
✅ **Checkout**: Customers can choose shipping or pickup  
✅ **No Shipping Fee**: Pickup orders automatically have $0 shipping  
✅ **Order Display**: Admin order list shows fulfillment method and pickup location  
✅ **Flexible**: Works with or without pickup locations (if none exist, only shipping is available)

## Setup Steps

### 1. Run Database Migrations

After pulling the latest code, create and run migrations:

```bash
# On EC2
cd ~/online-fitness-store-M
git pull origin main

# Inside Docker container
docker compose -f docker-compose.prod.yml exec web python manage.py makemigrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 2. Add Pickup Locations in Admin

1. Log into Django Admin: `https://fitness.lwsoc.com/admin/`
2. Go to **Orders** → **Pickup Locations**
3. Click **Add Pickup Location**
4. Fill in the details:
   - **Name**: e.g., "Main Store", "Downtown Branch"
   - **Address**: Full address details
   - **Phone**: Contact number (optional)
   - **Instructions**: Special instructions for customers (optional)
   - **Is Active**: Check this to make it available to customers
   - **Display Order**: Lower numbers appear first (optional)
5. Click **Save**

### 3. Test the Feature

1. Add physical products to cart
2. Go to checkout
3. You should see:
   - Radio buttons: "Ship to Address" and "Pick Up at Location"
   - When "Pick Up at Location" is selected:
     - Shipping form is hidden
     - Pickup location dropdown appears
     - Shipping fee becomes $0.00
   - When a pickup location is selected, its details are shown

## How It Works

### For Customers

1. **At Checkout**: Choose between "Ship to Address" or "Pick Up at Location"
2. **If Shipping**: Fill in shipping address (pre-filled from profile)
3. **If Pickup**: Select a pickup location from the dropdown
4. **Shipping Fee**: Automatically $0.00 for pickup orders

### For Admins

1. **Order List**: Shows "Method" column (Pickup/Shipping) and "Pickup Location" column
2. **Order Detail**: Shows fulfillment method and full pickup location address if applicable
3. **Pickup Locations**: Manage locations in admin panel

## Database Models

### PickupLocation Model

- Stores pickup location information
- Can be activated/deactivated
- Has display order for sorting

### Order Model Updates

- `is_pickup`: Boolean field indicating if order is pickup
- `pickup_location`: Foreign key to PickupLocation (nullable)

## Code Changes Summary

1. **`orders/models.py`**:
   - Added `PickupLocation` model
   - Added `is_pickup` and `pickup_location` fields to `Order`

2. **`orders/forms.py`**:
   - Added `fulfillment_method` radio field
   - Added `pickup_location_id` dropdown
   - Added validation to require pickup location when pickup is selected

3. **`payment/views.py`**:
   - Updated `_calc_shipping()` to accept `is_pickup` parameter
   - Updated checkout view to handle pickup selection
   - Saves pickup location to order

4. **`templates/payment/checkout.html`**:
   - Added fulfillment method selection
   - Added JavaScript to toggle between shipping and pickup sections
   - Shows pickup location details when selected

5. **`orders/admin.py`**:
   - Added `PickupLocationAdmin`
   - Updated `OrderAdmin` to show pickup information

## Notes

- **Digital/Service Products**: Pickup option only appears if cart contains physical products
- **No Locations**: If no active pickup locations exist, only shipping option is shown
- **Shipping Address**: For pickup orders, the order still stores address info (from pickup location) for record-keeping
- **Backward Compatible**: Existing orders without pickup info will continue to work

## Troubleshooting

### Pickup locations not showing in checkout

- Check that locations are marked as "Is Active" in admin
- Verify migrations have been run
- Check browser console for JavaScript errors

### Shipping fee not zero for pickup

- Verify `is_pickup=True` is being saved to order
- Check that `_calc_shipping()` is receiving `is_pickup=True` parameter

### Form validation errors

- Ensure pickup location is selected when "Pick Up at Location" is chosen
- Ensure shipping address fields are filled when "Ship to Address" is chosen

