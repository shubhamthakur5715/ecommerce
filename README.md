# Django Dropshipping Store (Starter Project)

A functional Django starter for a dropshipping e-commerce store with:
- Product/category catalog and search
- Session-based cart
- Signup/login/logout
- Checkout and order creation
- Customer order history
- Django admin for products, suppliers, orders, categories and coupons
- Supplier and fulfillment tracking fields
- Indian PIN-code field, optional GSTIN capture, INR currency and Asia/Kolkata timezone
- Razorpay Checkout test-mode integration with server-side signature verification
- Supplier purchase order records managed through Django admin
- Responsive starter storefront

## 1. Setup (Windows 11)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000 and admin at http://127.0.0.1:8000/admin/.

If PowerShell blocks activation, use `venv\Scripts\activate.bat` from Command Prompt.

## 2. Important notes before launch
This is a development starter, not a finished production deployment. Payment is intentionally not marked as paid by the checkout form. Integrate and verify Razorpay/Stripe server-side before accepting online payments. Configure email, HTTPS, backups, privacy/returns policies, shipping rates, tax rules and supplier API integration before going live.

## 3. Main routes
- `/` storefront
- `/products/` catalog/search
- `/products/<slug>/` product detail
- `/cart/` cart
- `/checkout/` checkout (login required)
- `/my-orders/` customer orders (login required)
- `/accounts/signup/` registration
- `/admin/` admin management

## 4. Dropshipping flow
Admin adds suppliers and products, customer places order, admin reviews the order and records supplier/fulfillment details, then adds carrier and tracking number. This starter does not automatically place orders with third-party suppliers; that requires a supplier API or approved integration.


## Razorpay test mode
1. Create a Razorpay account and use **test mode** keys.
2. Put `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env`.
3. Install requirements again: `pip install -r requirements.txt`.
4. Restart the development server and choose Online payment at checkout.
5. Test successful, failed and dismissed payments using Razorpay's current test instructions. Never commit `.env` or expose the secret in frontend code.

The browser verification endpoint checks Razorpay's payment signature, but for production also implement Razorpay webhooks, idempotency, reconciliation and refund handling. Payment confirmation should be resilient to duplicate callbacks.

## Supplier purchase orders
Open Admin → Supplier purchase orders. Create a purchase order linked to a customer order and supplier, then add items, quantities and supplier costs. This is manual supplier fulfillment; it does not transmit orders to supplier systems automatically.

## Indian tax and shipping
GSTIN is an optional field only. This starter does not calculate GST or generate legally compliant GST invoices. Confirm tax treatment, invoice requirements, COD remittance, consumer protection disclosures and return policy with a qualified Indian tax/compliance professional before launch.
