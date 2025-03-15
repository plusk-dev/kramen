import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request, Depends
import stripe
from fastapi.responses import JSONResponse
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from schemas.dungo_schemas.payments import CheckoutRequest
from models import User, session
from utils.auth import verify_token  # Assuming you have an auth system in place

payments_router = APIRouter()

# Stripe Configuration

stripe.api_key = STRIPE_SECRET_KEY

# Pydantic model for request body


@payments_router.post("/checkout")
async def checkout(request: Request, checkout_request: CheckoutRequest, user: dict = Depends(verify_token)):

    if not checkout_request.price_id:
        raise HTTPException(
            status_code=400, detail="Missing price_id in request body")

    try:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": checkout_request.price_id,
                    "quantity": 1,
                },
            ],
            customer_email=user["email"],
            mode="subscription",
            success_url="https://kramen.tech/dashboard",
            cancel_url="https://kramen.tec/dashboard",
        )
        return JSONResponse(content={"session_id": session.id})
    except Exception as e:
        print("Error creating checkout session:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@payments_router.post("/webhook")
async def webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    if not stripe_signature:
        raise HTTPException(
            status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event.type == "customer.subscription.created":
        subscription = event.data.object
        customer = stripe.Customer.retrieve(subscription.customer)
        customer_email = customer.email
        price_details = subscription['items']['data'][0]['price']
        if price_details['product'] == '':
            limit = int(price_details['metadata'].get("limit", 0))
            update_user_limit(customer_email, limit)
        else:
            return JSONResponse(content={"message": "event not for kramen"})

    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        customer = stripe.Customer.retrieve(subscription.customer)
        customer_email = customer.email
        price_details = subscription['items']['data'][0]['price']
        if price_details['product'] == '':
            limit = int(price_details['metadata'].get("limit", 0))
            update_user_limit(customer_email, 0)
        else:
            return JSONResponse(content={"message": "event not for kramen"})

    return JSONResponse(content={"message": "ok"}, status_code=200)


def update_user_limit(email: str, limit: int):
    user = session.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=400, detail={
            "message": "user with this email does not exist"
        })

    user.limit = limit
    session.commit()
