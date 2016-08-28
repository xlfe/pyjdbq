
fields = []
with open('./schema.txt','r') as schema:

    for field in schema:

        field = field.strip()
        if field.endswith(','):
            field = field[:-1]

        try:
            name, t = field.split(':')
        except:
            name = field

        fields.append(name)

print fields
