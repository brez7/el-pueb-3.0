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
        base_amount = int(people) * 18 * 100
        return redirect(
            url_for(
                "checkout",
                total_amount=total_amount,
                base_amount=base_amount,
                people=people,
                date=date,
                time=time,
                items=json.dumps(items),
            )
        )
    people = request.args.get("people")
    base_amount = int(people) * 18 * 100
    return render_template("menu.html", people=people, base_amount=base_amount)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        data = request.get_json()
        total_amount = int(data["total_amount"])
        base_amount = int(data["base_amount"])
        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount + base_amount,
            currency="usd",
            payment_method_types=["card"],
        )
        return jsonify({"clientSecret": payment_intent["client_secret"]})

    items = json.loads(request.args.get("items"))
    total_amount = int(request.args.get("total_amount"))
    base_amount = int(request.args.get("base_amount"))
    people = int(request.args.get("people"))
    date = request.args.get("date")
    time = request.args.get("time")

    return render_template(
        "checkout.html",
        items=items,
        total_amount=total_amount,
        base_amount=base_amount,
        people=people,
        date=date,
        time=time,
    )


@app.route("/success")
def success():
    return redirect(
        url_for(
            "summary",
            email=request.args.get("email"),
            first_name=request.args.get("first_name"),
            last_name=request.args.get("last_name"),
            address=request.args.get("address"),
            city=request.args.get("city"),
            state=request.args.get("state"),
            zip=request.args.get("zip"),
            phone=request.args.get("phone"),
            people=request.args.get("people"),
            date=request.args.get("date"),
            time=request.args.get("time"),
            items=request.args.get("items"),
            total_amount=request.args.get("total_amount"),
            base_amount=request.args.get("base_amount"),
        )
    )


@app.route("/summary")
def summary():
    try:
        people = request.args.get("people")
        date = request.args.get("date")
        time = request.args.get("time")
        address = request.args.get("address")
        city = request.args.get("city")
        state = request.args.get("state")
        zip_code = request.args.get("zip")
        phone = request.args.get("phone")
        email = request.args.get("email")
        items = json.loads(request.args.get("items"))
        total_amount = int(request.args.get("total_amount"))
        base_amount = int(request.args.get("base_amount"))

        grand_total = total_amount + base_amount

        order_details = (
            f"Order Details:\nPeople: {people}\nDate: {date}\nTime: {time}\n"
            f"Address: {address}, {city}, {state} {zip_code}\nPhone: {phone}\nEmail: {email}\nItems:\n"
            + "\n".join(
                [
                    f"{item['name']} (x{item['quantity']}) - ${item['price'] / 100}"
                    for item in items
                ]
            )
            + f"\nTotal Amount for Selected Items: ${total_amount / 100:.2f}"
            + f"\nBase Amount for Catering: ${base_amount / 100:.2f}"
            + f"\nGrand Total: ${grand_total / 100:.2f}"
        )

        msg_to_restaurant = Message(
            "New Catering Order",
            sender="rbresnik@gmail.com",
            recipients=["rob@elpueblomex.com"],
        )
        msg_to_restaurant.body = order_details
        mail.send(msg_to_restaurant)

        msg_to_customer = Message(
            "Your Catering Order Confirmation",
            sender="rbresnik@gmail.com",
            recipients=[email],
        )
        msg_to_customer.body = f"Thank you for your order!\n\n{order_details}"
        mail.send(msg_to_customer)

        return render_template(
            "summary.html",
            people=people,
            date=date,
            time=time,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            email=email,
            items=items,
            total_amount=total_amount,
            base_amount=base_amount,
            grand_total=grand_total,
        )
    except Exception as e:
        return str(e), 500


if __name__ == "__main__":
    app.run(debug=True)
