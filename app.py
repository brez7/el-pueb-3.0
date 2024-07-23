from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe
from flask_mail import Mail, Message
from datetime import datetime
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


# Custom filter to format datetime
@app.template_filter("strftime")
def format_datetime(value, format="%m-%d-%Y"):
    if value is None:
        return ""
    return value.strftime(format)


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
        meat1 = request.form.get("meat1")
        meat2 = request.form.get("meat2")
        items = [
            {
                "name": meat1,
                "quantity": 1,
            },
            {
                "name": meat2,
                "quantity": 1,
            },
        ]
        people = request.args["people"]
        date = request.args["date"]
        time = request.args["time"]
        base_amount = int(people) * 1800  # Base amount calculation
        total_amount = 0  # Total amount is zero for now

        return redirect(
            url_for(
                "checkout",
                total_amount=total_amount,
                base_amount=base_amount,
                people=people,
                date=date,
                time=time,
                items=json.dumps(items),
                meat1=meat1,
                meat2=meat2,
            )
        )
    people = request.args.get("people")
    base_amount = int(people) * 1800
    return render_template("menu.html", people=people, base_amount=base_amount)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        data = request.get_json()

        if data is None:
            return jsonify({"error": "Invalid JSON received"}), 400

        total_amount = data.get("total_amount")
        base_amount = data.get("base_amount")

        if total_amount is None or base_amount is None:
            return jsonify({"error": "Missing amount data"}), 400

        try:
            total_amount = int(total_amount)
            base_amount = int(base_amount)
        except ValueError:
            return jsonify({"error": "Invalid amount data"}), 400

        try:
            if total_amount > 0:
                payment_intent = stripe.PaymentIntent.create(
                    amount=total_amount,
                    currency="usd",
                    payment_method_types=["card"],
                )
                return jsonify({"clientSecret": payment_intent["client_secret"]})
            else:
                # No payment intent needed, but return a dummy client secret for consistency
                return jsonify({"clientSecret": "dummy_client_secret"})
        except Exception as e:
            print(f"Error creating payment intent: {e}")  # Log the error to the console
            return jsonify({"error": str(e)}), 500

    try:
        people = request.args.get("people")
        date = datetime.strptime(request.args.get("date"), "%Y-%m-%d")
        time = request.args.get("time")
        meat1 = request.args.get("meat1")
        meat2 = request.args.get("meat2")
        items = request.args.get("items")
        if items is None:
            items = []
        else:
            items = json.loads(items)
        total_amount = int(
            request.args.get("total_amount")
        )  # Ensure this is an integer
        base_amount = int(request.args.get("base_amount"))  # Ensure this is an integer
    except Exception as e:
        print(
            f"Error processing request parameters: {e}"
        )  # Log the error to the console
        return jsonify({"error": str(e)}), 400

    return render_template(
        "checkout.html",
        people=people,
        date=date,
        time=time,
        meat1=meat1,
        meat2=meat2,
        items=items,
        total_amount=total_amount,
        base_amount=base_amount,
        meat_choices={
            "carne_asada": "Carne Asada",
            "chicken": "Chicken",
            "adobada": "Adobada",
        },
    )


@app.route("/success")
def success():
    # Retrieve order details from query parameters
    people = request.args.get("people")
    date = request.args.get("date")
    date = datetime.strptime(date, "%Y-%m-%d")
    time = request.args.get("time")
    items = request.args.get("items")
    if items is not None:
        items = json.loads(items)
    else:
        items = []
    total_amount = request.args.get("total_amount")
    base_amount = request.args.get("base_amount")
    meat1 = request.args.get("meat1")
    meat2 = request.args.get("meat2")
    customer_email = request.args.get("email")

    # Prepare email content
    order_details = {
        "people": people,
        "date": date,
        "time": time,
        "items": items,
        "total_amount": total_amount,
        "base_amount": base_amount,
        "meat1": meat1,
        "meat2": meat2,
        "customer_email": customer_email,
        "meat_choices": {
            "carne_asada": "Carne Asada",
            "chicken": "Chicken",
            "adobada": "Adobada",
        },
    }

    # Send email to the restaurant
    msg_to_restaurant = Message(
        "New Catering Order",
        sender="rbresnik@gmail.com",
        recipients=["rob@elpueblomex.com"],
    )
    msg_to_restaurant.body = f"Order Details:\nPeople: {people}\nDate: {date.strftime('%m-%d-%Y')}\nTime: {time}\n"
    for item in items:
        msg_to_restaurant.body += f"{item['name']} (x{item['quantity']})\n"
    msg_to_restaurant.body += f"Base Amount: ${int(base_amount) / 100:.2f}\n"
    msg_to_restaurant.body += f"First Meat Choice: {meat1}\n"
    msg_to_restaurant.body += f"Second Meat Choice: {meat2}\n"
    mail.send(msg_to_restaurant)

    # Send email to the customer
    msg_to_customer = Message(
        "Your Catering Order Confirmation",
        sender="rbresnik@gmail.com",
        recipients=[customer_email],
    )
    msg_to_customer.body = f"Thank you for your order!\n\nOrder Details:\nPeople: {people}\nDate: {date.strftime('%m-%d-%Y')}\nTime: {time}\n"
    for item in items:
        msg_to_customer.body += f"{item['name']} (x{item['quantity']})\n"
    msg_to_customer.body += f"Base Amount: ${int(base_amount) / 100:.2f}\n"
    msg_to_customer.body += f"First Meat Choice: {meat1}\n"
    msg_to_customer.body += f"Second Meat Choice: {meat2}\n"
    mail.send(msg_to_customer)

    return render_template("summary.html", **order_details)


if __name__ == "__main__":
    app.run(debug=True)
