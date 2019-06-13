# MoosendFDW

A [Multicorn](https://multicorn.org/)-based foreign data wrapper for the Moosend
API.

Why? Because I want to control my mailing lists from postgresql; because I want
postgresql to *be* my API; because [Graphile](https://www.graphile.org/) makes
it possible for me to design a database model and use it as my API.

## Install

Assuming you have the Multicorn extension and python setuptools installed on
your Postgresql server, run the following to install this module:

```bash
git clone https://github.com/mdiin/moosend-fdw
cd moosend-fdw
sudo python setup.py install
```

Following that, restart your postgresql server to make the module accessible.

## Usage

To create the foreign data wrapper server:

```sql
CREATE SERVER moosend
FOREIGN DATA WRAPPER multicorn
OPTIONS (
  wrapper 'moosendfdw.SubscriberFDW'
);
```

To create a foreign table using this server:

```sql
CREATE FOREIGN TABLE moosend_subscribers (
  "ID" TEXT COMMENT 'Maps directly to the ID property in Moosend',
  "Email" TEXT COMMENT 'Maps directly to the Email property in Moosend',
  "Name" TEXT COMMEN 'Maps directly to the Name property in Moosend',
  "CreatedOn" TIMESTAMP WITH TIME ZONE COMMENT 'Maps directly to the CreatedOn property in Moosend',
  "MyCrazyNumber" INTEGER COMMENT 'Maps to the MyCrazyNumber custom field on the mailing list'
)
SERVER moosend
OPTIONS (
  api_key 'your_api_key',
  list_id 'your_list_id'
)
```

Now all your list subscribers are but a `SELECT` away:

```sql
SELECT * FROM moosend_subscribers;
```

And you can `INSERT`, `UPDATE`, and `DELETE` as on a regular table.

## Column names

Column names of your foreign table that do not match a Moosend-internal field
are assumed to be custom fields in the terminology of Moosend. What this means
is that your table's columns for e.g. subscriber email must match what the
Moosend API calls them.

See the [Moosend Subscribers API
documentation](https://moosendapp.docs.apiary.io/#reference/subscribers) for
details on the column names.

## A note on subscriber consent

When inserting a subscriber using this foreign data wrapper the assumption is
that you have received an opt-in confirmation from somewhere other than Moosend.

## Authors

- **Matthias Varberg Ingesman** - *Initial work* - [mdiin](https://github.com/mdiin)

See also the list of [contributers](https://github.com/mdiin/moosend-fdw/contributers) who participated in this project.

## License

This project is licensed under the MIT license - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Multicorn](https://multicorn.org) for building an amazing framework for Postgresql foreign data wrappers
- [Moosend](https://moosend.com) for being a friendly email service
