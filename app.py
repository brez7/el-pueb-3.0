import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe
from flask_mail import Mail, Message
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
stripe.api_key = "f"

# Configure Flask-Mail with Gmail SMTP server using TLS
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "rbresnik@gmail.com"
app.config["MAIL_PASSWORD"] = (
    "f"  # Use the provided app-specific password
)
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

# Configure SQLAlchemy
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    BASE_DIR, "catering.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

meat_choices = {
    "carne_asada": "Carne Asada",
    "chicken": "Chicken",
    "adobada": "Adobada",
    # Add more mappings if needed
}


# Custom filter to format datetime
@app.template_filter("strftime")
def format_datetime(value, format="%m-%d-%Y"):
    if value is None:
        return ""
    return value.strftime(format)


# Ensure tables are created before the first request
@app.before_first_request
def create_tables():
    db.create_all()


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    people = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    base_amount = db.Column(db.Integer, nullable=False)
    sub_total = db.Column(db.Integer, nullable=False)
    tax = db.Column(db.Integer, nullable=False)
    grand_total = db.Column(db.Integer, nullable=False)
    meat1 = db.Column(db.String(50), nullable=False)
    meat2 = db.Column(db.String(50), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    items = db.relationship("Item", backref="order", lazy=True)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)


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
        add_ons = []

        additional_meat_choice = request.form.get("additional_meat_choice")
        if additional_meat_choice and additional_meat_choice not in {meat1, meat2}:
            add_ons.append(
                {
                    "name": f"Additional Meat Choice: {meat_choices.get(additional_meat_choice, additional_meat_choice)}",
                    "price": 3000,
                    "quantity": 1,
                }
            )

        if request.form.get("quesadillas"):
            add_ons.append({"name": "Quesadillas", "price": 3000, "quantity": 1})

        if request.form.get("shrimp"):
            add_ons.append({"name": "Shrimp", "price": 4000, "quantity": 1})

        if request.form.get("sour_cream"):
            add_ons.append({"name": "Sour Cream", "price": 2000, "quantity": 1})

        if request.form.get("buneolos"):
            add_ons.append({"name": "Buneolos", "price": 2000, "quantity": 1})

        if request.form.get("onions_cilantro"):
            add_ons.append({"name": "Add Onions/Cilantro", "price": 0, "quantity": 1})

        items = [
            {"name": meat_choices.get(meat1, meat1), "price": 0, "quantity": 1},
            {"name": meat_choices.get(meat2, meat2), "price": 0, "quantity": 1},
        ] + add_ons

        people = request.args["people"]
        date = request.args["date"]
        time = request.args["time"]
        base_amount = int(people) * 1800  # Base amount calculation
        total_amount = sum(item["price"] * item["quantity"] for item in add_ons)
        sub_total = base_amount + total_amount
        tax = sub_total * 0.0775
        grand_total = sub_total + tax

        return redirect(
            url_for(
                "checkout",
                total_amount=total_amount,
                base_amount=base_amount,
                sub_total=sub_total,
                tax=tax,
                grand_total=grand_total,
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
        sub_total = data.get("sub_total")
        tax = data.get("tax")
        grand_total = data.get("grand_total")

        if (
            total_amount is None
            or base_amount is None
            or sub_total is None
            or tax is None
            or grand_total is None
        ):
            return jsonify({"error": "Missing amount data"}), 400

        try:
            total_amount = int(total_amount)
            base_amount = int(base_amount)
            sub_total = int(sub_total)
            tax = int(tax)
            grand_total = int(grand_total)
        except ValueError:
            return jsonify({"error": "Invalid amount data"}), 400

        try:
            if grand_total > 0:
                payment_intent = stripe.PaymentIntent.create(
                    amount=grand_total,
                    currency="usd",
                    payment_method_types=["card"],
                )
                return jsonify({"clientSecret": payment_intent["client_secret"]})
            else:
                return jsonify({"clientSecret": "dummy_client_secret"})
        except Exception as e:
            print(f"Error creating payment intent: {e}")
            return jsonify({"error": str(e)}), 500

    try:
        people = request.args.get("people")
        date = datetime.strptime(request.args.get("date"), "%Y-%m-%d")
        time = request.args.get("time")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        meat1 = request.args.get("meat1")
        meat2 = request.args.get("meat2")
        items = request.args.get("items")
        if items is None:
            items = []
        else:
            items = json.loads(items)
        total_amount = int(request.args.get("total_amount"))
        base_amount = int(request.args.get("base_amount"))
        sub_total = float(request.args.get("sub_total"))
        tax = float(request.args.get("tax"))
        grand_total = float(request.args.get("grand_total"))
    except Exception as e:
        print(f"Error processing request parameters: {e}")
        return jsonify({"error": str(e)}), 400

    formatted_items = [
        {
            "name": meat_choices.get(item["name"], item["name"]),
            "price": item["price"],
            "quantity": item["quantity"],
        }
        for item in items
        if item["name"] not in {meat_choices.get(meat1), meat_choices.get(meat2)}
    ]

    return render_template(
        "checkout.html",
        people=people,
        date=date,
        time=time,
        first_name=first_name,
        last_name=last_name,
        meat1=meat_choices.get(meat1, meat1),
        meat2=meat_choices.get(meat2, meat2),
        items=formatted_items,
        total_amount=total_amount,
        base_amount=base_amount,
        sub_total=sub_total,
        tax=tax,
        grand_total=grand_total,
        meat_choices=meat_choices,
    )


@app.route("/success")
def success():
    try:
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
        sub_total = request.args.get("sub_total")
        tax = request.args.get("tax")
        grand_total = request.args.get("grand_total")
        meat1 = request.args.get("meat1")
        meat2 = request.args.get("meat2")
        customer_email = request.args.get("email")
        first_name = request.args.get("first_name")
        last_name = request.args.get("last_name")
        address = request.args.get("address")
        city = request.args.get("city")
        state = request.args.get("state")
        zip_code = request.args.get("zip")
        phone = request.args.get("phone")

        formatted_items = [
            {
                "name": meat_choices.get(item["name"], item["name"]),
                "price": item["price"],
                "quantity": item["quantity"],
            }
            for item in items
            if item["name"] not in {meat_choices.get(meat1), meat_choices.get(meat2)}
        ]

        # Save order to the database
        order = Order(
            people=people,
            date=date,
            time=time,
            total_amount=total_amount,
            base_amount=base_amount,
            sub_total=sub_total,
            tax=tax,
            grand_total=grand_total,
            meat1=meat1,
            meat2=meat2,
            customer_email=customer_email,
            first_name=first_name,
            last_name=last_name,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
        )
        db.session.add(order)
        db.session.commit()

        # Save items to the database
        for item in formatted_items:
            order_item = Item(
                name=item["name"],
                price=item["price"],
                quantity=item["quantity"],
                order_id=order.id,
            )
            db.session.add(order_item)

        db.session.commit()

        order_details = {
            "people": people,
            "date": date,
            "time": time,
            "items": formatted_items,
            "total_amount": total_amount,
            "base_amount": base_amount,
            "sub_total": sub_total,
            "tax": tax,
            "grand_total": grand_total,
            "meat1": meat_choices.get(meat1, meat1),
            "meat2": meat_choices.get(meat2, meat2),
            "customer_email": customer_email,
            "first_name": first_name,
            "last_name": last_name,
            "address": address,
            "city": city,
            "state": state,
            "zip": zip_code,
            "phone": phone,
            "meat_choices": meat_choices,
        }

        def format_item(item):
            price = f"${item['price'] / 100:.2f}" if item["price"] > 0 else ""
            return f"<tr><td style='font-weight:bold; padding-right: 5px;'>{item['name']}</td><td>{price}</td></tr>"

        customer_email_body = f"""
        <html>
        <body>
        <h1>El Pueblo Mexican Food Catering Order</h1>
        <h2>Thank you for your order!</h2>
        <table style="width:50%; border-collapse:collapse;">
          <tr><th colspan="2" style="text-align:left;">ORDER RECEIPT</th></tr>
          <tr><td colspan="2" style="text-align:left;">Order Details:</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">First Name:</td><td style="text-align:left;">{first_name}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Last Name:</td><td style="text-align:left;">{last_name}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">People:</td><td style="text-align:left;">{people}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5 px;">Date:</td><td style="text-align:left;">{date.strftime('%m-%d-%Y')}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Time:</td><td style="text-align:left;">{time}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Address:</td><td style="text-align:left;">{address}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">City:</td><td style="text-align:left;">{city}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">State:</td><td style="text-align:left;">{state}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Zip:</td><td style="text-align:left;">{zip_code}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Phone:</td><td style="text-align:left;">{phone}</td></tr>
          <tr><td colspan="2" style="text-align:left;">Items Ordered:</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">First Meat Choice:</td><td style="text-align:left;">{meat_choices.get(meat1, meat1)}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Second Meat Choice:</td><td style="text-align:left;">{meat_choices.get(meat2, meat2)}</td></tr>
          <tr><td colspan="2" style="text-align:left;">Additional Items:</td></tr>
          {''.join(format_item(item) for item in formatted_items)}
          <tr><td colspan="2" style="text-align:left;">Summary:</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5 px;">Base Amount:</td><td style="text-align:left;">${int(base_amount) / 100:.2f}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Sub-total:</td><td style="text-align:left;">${float(sub_total) / 100:.2f}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Tax (7.75%):</td><td style="text-align:left;">${float(tax) / 100:.2f}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">Grand Total:</td><td style="text-align:left;">${float(grand_total) / 100:.2f}</td></tr>
        </table>
        <p>Thank you for choosing El Pueblo Mexican Food for your catering needs!</p>
        </body>
        </html>
        """

        restaurant_email_body = f"""
        <html>
        <body>
        <h2>Order Details for {first_name} {last_name} </h2>
        <table style="width:50%; border-collapse:collapse;">
          <tr><th colspan="2" style="text-align:left;">ORDER RECEIPT</th></tr>
          <tr><td colspan="2" style="text-align:left;">Order Details:</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">First Name:</td><td style="text-align:left;">{first_name}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5px;">Last Name:</td><td style="text-align:left;">{last_name}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5px;">People:</td><td style="text-align:left;">{people}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Date:</td><td style="text-align:left;">{date.strftime('%m-%d-%Y')}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5 px;">Time:</td><td style="text-align:left;">{time}</td></tr>
          <tr><td style="font-weight:bold;text-align:left; padding-right: 5 px;">Address:</td><td style="text.align:left;">{address}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">City:</td><td style="text-align:left;">{city}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">State:</td><td style="text.align:left;">{state}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Zip:</td><td style="text.align:left;">{zip_code}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Phone:</td><td style="text-align:left;">{phone}</td></tr>
          <tr><td colspan="2" style="text-align:left;">Items Ordered:</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">First Meat Choice:</td><td style="text.align:left;">{meat_choices.get(meat1, meat1)}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Second Meat Choice:</td><td style="text-align:left;">{meat_choices.get(meat2, meat2)}</td></tr>
          <tr><td colspan="2" style="text-align:left;">Additional Items:</td></tr>
          {''.join(format_item(item) for item in formatted_items)}
          <tr><td colspan="2" style="text.align:left;">Summary:</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Base Amount:</td><td style="text-align:left;">${int(base_amount) / 100:.2f}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Sub-total:</td><td style="text.align:left;">${float(sub_total) / 100:.2f}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Tax (7.75%):</td><td style="text.align:left;">${float(tax) / 100:.2f}</td></tr>
          <tr><td style="font-weight:bold;text.align:left; padding-right: 5 px;">Grand Total:</td><td style="text.align:left;">${float(grand_total) / 100:.2f}</td></tr>
        </table>
        </body>
        </html>
        """

        # Send email to the customer
        msg_to_customer = Message(
            "Your Catering Order Confirmation",
            sender="rbresnik@gmail.com",
            recipients=[customer_email],
        )
        msg_to_customer.html = customer_email_body
        mail.send(msg_to_customer)

        # Send email to the restaurant
        msg_to_restaurant = Message(
            "New Catering Order",
            sender="rbresnik@gmail.com",
            recipients=["rob@elpueblomex.com"],
        )
        msg_to_restaurant.html = restaurant_email_body
        mail.send(msg_to_restaurant)

        return render_template("summary.html", **order_details)
    except Exception as e:
        print(f"Error processing success route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/orders")
def orders():
    all_orders = Order.query.all()
    return render_template("orders.html", orders=all_orders, meat_choices=meat_choices)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)
