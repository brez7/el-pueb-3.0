from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe
from flask_mail import Mail, Message
import json

app = Flask(__name__)
stripe.api_key = "sk_test_51HMJ15LkC2vPsGwFJOABaLMeVM3Wzvfa9TaHFtWbYwBw2G3mwwV76RN5rnAK3Z29uXwBxn9KyK8pzl1cYIGnxM1E00NlJJCFmT"

# Configure Flask-Mail with Gmail SMTP server using TLS
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "rbresnik@gmail.com"
app.config["MAIL_PASSWORD"] = (
    "dzybveqbvyjqbtch"  # Use the provided app-specific password
)
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

mail = Mail(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/event-details", methods=["GET", "POST"])
def event_details():
    if request.method == "POST":
        people = request.form["people"]
        date = request.form["date"]
        time = request.form["time"]
        return redirect(url_for("menu", people=people, date=date, time=time))
    return render_template("event_details.html")


@app.route("/menu", methods=["GET", "POST"])
def menu():
    if request.method == "POST":
        items = [
            {
                "name": "item1",
                "price": 2000,
                "quantity": int(request.form.get("item1_quantity", 0)),
            },
            {
                "name": "item2",
                "price": 3000,
                "quantity": int(request.form.get("item2_quantity", 0)),
            },
        ]
        total_amount = sum(item["price"] * item["quantity"] for item in items)
        people = request.args["people"]
        date = request.args["date"]
        time = request.args["time"]
        return redirect(
            url_for(
                "checkout",
                total_amount=total_amount,
                people=people,
                date=date,
                time=time,
                items=json.dumps(items),
            )
        )
    return render_template("menu.html")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        data = request.get_json()
        total_amount = data["total_amount"]
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount),
            currency="usd",
            payment_method_types=["card"],
        )
        return jsonify({"clientSecret": payment_intent["client_secret"]})
    items = json.loads(request.args.get("items"))
    total_amount = request.args.get("total_amount")
    return render_template("checkout.html", items=items, total_amount=total_amount)


@app.route("/success")
def success():
    # Retrieve order details
    people = request.args.get("people")
    date = request.args.get("date")
    time = request.args.get("time")
    items = json.loads(request.args.get("items"))
    total_amount = request.args.get("total_amount")
    customer_email = request.args.get(
        "email"
    )  # Assuming you collect this from the user

    # Prepare email content
    order_details = f"Order Details:\nPeople: {people}\nDate: {date}\nTime: {time}\n"
    for item in items:
        order_details += f"{item}\n"
    order_details += f"Total Amount: ${int(total_amount) / 100:.2f}"

    # Send email to the restaurant
    msg_to_restaurant = Message(
        "New Catering Order",
        sender="rbresnik@gmail.com",
        recipients=["rob@elpueblomex.com"],
    )
    msg_to_restaurant.body = order_details
    mail.send(msg_to_restaurant)

    # Send email to the customer
    msg_to_customer = Message(
        "Your Catering Order Confirmation",
        sender="rbresnik@gmail.com",
        recipients=[customer_email],
    )
    msg_to_customer.body = f"Thank you for your order!\n\n{order_details}"
    mail.send(msg_to_customer)

    return "Payment successful and emails sent!"


if __name__ == "__main__":
    app.run(debug=True)
