from extentions import db
from sqlalchemy.exc import SQLAlchemyError


def create_record(model, data_dict):
    """
     Create a new record in the database for the given model.
    """
    try:
        record = model(**data_dict)
        db.session.add(record)
        db.session.commit()
        return record
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e


def get_record_by(model, **filters):
    """
    Retrieve the first record that matches the given filters.
    """
    return model.query.filter_by(**filters).first()


def get_all_records(model, **filters):
    """
    Retrieve all records that match the given filters.
    """
    return model.query.filter_by(**filters)


def update_record(instance, update_data):
    """
    Update an existing record with new data.
    """
    try:
        for key, value in update_data.items():
            setattr(instance, key, value)
        db.session.commit()
        return instance
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e


def delete_record(instance):
    """
    Delete a record from the database.
    """
    try:
        db.session.delete(instance)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e


def create_multiple_records(model, data_list):
    """
    Bulk insert multiple records into the database.
    """
    try:
        records = [model(**data) for data in data_list]
        db.session.add_all(records)
        db.session.commit()
        return records
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e


