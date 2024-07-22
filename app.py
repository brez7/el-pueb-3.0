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

# Mapping dictionary
meat_choices = {
    "carne_asada": "Carne Asada",
    "chicken": "Chicken",
    "adobada": "Adobada",
}


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
        people = request.args["people"]
        date = request.args["date"]
        time = request.args["time"]
        base_amount = int(people) * 1800  # Base amount calculation
        total_amount = 0  # No additional items

        return redirect(
            url_for(
                "checkout",
                total_amount=total_amount,
                base_amount=base_amount,
                people=people,
                date=date,
                time=time,
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
        total_amount = int(data["total_amount"])
        base_amount = int(data["base_amount"])

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
            return jsonify({"error": str(e)}), 500

    people = request.args.get("people")
    date = request.args.get("date")
    time = request.args.get("time")
    meat1 = request.args.get("meat1")
    meat2 = request.args.get("meat2")
    total_amount = int(request.args.get("total_amount"))  # Ensure this is an integer
    base_amount = int(request.args.get("base_amount"))  # Ensure this is an integer

    return render_template(
        "checkout.html",
        people=people,
        date=date,
        time=time,
        meat1=meat1,
        meat2=meat2,
        total_amount=total_amount,
        base_amount=base_amount,
        meat_choices=meat_choices,
    )


@app.route("/success")
def success():
    people = request.args.get("people")
    date = request.args.get("date")
    time = request.args.get("time")
    total_amount = request.args.get("total_amount")
    base_amount = request.args.get("base_amount")
    meat1 = request.args.get("meat1")
    meat2 = request.args.get("meat2")
    customer_email = request.args.get("email")

    order_details = {
        "people": people,
        "date": date,
        "time": time,
        "total_amount": total_amount,
        "base_amount": base_amount,
        "meat1": meat1,
        "meat2": meat2,
        "customer_email": customer_email,
        "meat_choices": meat_choices,
    }

    msg_to_restaurant = Message(
        "New Catering Order",
        sender="rbresnik@gmail.com",
        recipients=["rob@elpueblomex.com"],
    )
    msg_to_restaurant.body = (
        f"Order Details:\nPeople: {people}\nDate: {date}\nTime: {time}\n"
    )
    msg_to_restaurant.body += (
        f"Total Amount for Additional Items: ${int(total_amount) / 100:.2f}\n"
    )
    msg_to_restaurant.body += (
        f"Base Amount for Catering: ${int(base_amount) / 100:.2f}\n"
    )
    msg_to_restaurant.body += f"First Meat Choice: {meat_choices[meat1]}\n"
    msg_to_restaurant.body += f"Second Meat Choice: {meat_choices[meat2]}\n"
    mail.send(msg_to_restaurant)

    msg_to_customer = Message(
        "Your Catering Order Confirmation",
        sender="rbresnik@gmail.com",
        recipients=[customer_email],
    )
    msg_to_customer.body = f"Thank you for your order!\n\nOrder Details:\nPeople: {people}\nDate: {date}\nTime: {time}\n"
    msg_to_customer.body += (
        f"Total Amount for Additional Items: ${int(total_amount) / 100:.2f}\n"
    )
    msg_to_customer.body += f"Base Amount for Catering: ${int(base_amount) / 100:.2f}\n"
    msg_to_customer.body += f"First Meat Choice: {meat_choices[meat1]}\n"
    msg_to_customer.body += f"Second Meat Choice: {meat_choices[meat2]}\n"
    mail.send(msg_to_customer)

    return render_template("summary.html", **order_details)


if __name__ == "__main__":
    app.run(debug=True)
