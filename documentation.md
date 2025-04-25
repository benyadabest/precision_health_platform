Patient
View in 

benshvartsman1 Ontology


Python


1.188

Description
Patient 'EHR'
Properties
Property
API Name

Type	Description
Id

id	

String
No description
Name

name	

String
No description
Alert Status
alertStatus	

String
AIP-generated classification of the patient's current condition: Green (stable), Yellow (monitor), Red (urgent)
Assigned Doctor
assignedDoctor	

String
No description
Condition
condition	

String
No description
Data Donation
dataDonation	

String
No description
Dob
dob	

Date
No description
Status
status	

String
No description
Treatment
treatment	

String
No description

Load single Patient
Parameters
primaryKey
string
The primary key of the Patient you want to fetch
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient/{primaryKey}

result = client.ontology.objects.Patient.get("primaryKey")

Load pages of Patients
Load a list of objects of a requested page size, after a given page token if present.
Note that this endpoint leverages the underlying object syncing technology used for the object type. If Patient is backed by Object Storage V2, there is no request limit. If it is backed by Phonograph, there is a limit of 10,000 results – when more than 10,000 Patients have been requested, a ObjectsExceededLimit error will be thrown.
Parameters
pageSize
integer
(optional)
The size of the page to request up to a maximum of 10,000. If not provided, will load up to 10,000 Patients. The pageSize of the initial page is used for subsequent pages.
pageToken
string
(optional)
If provided, will request a page with size less than or equal to the pageSize of the first requested page.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient

result = client.ontology.objects.Patient.page(page_size=30, page_token=None)
page_token = result.next_page_token
data = result.data

Load all Patients
Loads all Patients. Depending on the language, results could be a list with all rows or an iterator to loop through all rows.
Note that this endpoint leverages the underlying object syncing technology used for the object type. If Patient is backed by Object Storage V2, there is no request limit. If it is backed by Phonograph, there is a limit of 10,000 results – when more than 10,000 Patients have been requested, a ObjectsExceededLimit error will be thrown.
POST
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objectSets/loadObjects

objects_iterator = client.ontology.objects.Patient.iterate()
objects = list(objects_iterator)

Load ordered results
Load an ordered list of Patients by specifying a sort direction for specific properties. When calling via APIs, sorting criteria are specified via the fields array. When calling via SDKs, you can chain multiple orderBy calls together. The sort order for strings is case-sensitive, meaning numbers will come before uppercase letters, which will come before lowercase letters. For example, "Cat" will come before "bat".
Parameters
field
string
The property you want to sort by. With the SDK, this is provided for you via a sortBy interface.
direction
asc
|
desc
The direction you want to sort in, either ascending or descending. With the SDK, this is provided via the asc() and desc() functions on the sortBy interface.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient

from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient

client.ontology.objects.Patient.where(~Patient.object_type.name.is_null()).order_by(Patient.object_type.name.asc()).iterate()

Load link by primary key
SELECT LINK TYPE



PROEntity

Go from an instance of Patient to a single instance of PROEntity via a primary key of PROEntity.
Parameters
primaryKey
string
Primary key of Patient to start from. If loading via the SDK, this is assumed via a previous .get() call.
linkedObjectPrimaryKey
string
Primary key of PROEntity to fetch.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient/{primaryKey}/links/Proentity/{linkedObjectPrimaryKey}

from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient

def get_linked_Proentity(source: Patient, linkedObjectPrimaryKey: string):
    return source.proentities.get(linkedObjectPrimaryKey)

Load linked Vitals
SELECT LINK TYPE



Vitals

Load linked Vitals from an instance of Patient
Parameters
primaryKey
string
Primary key of Patient to start from. If loading via the SDK, this is assumed via a previous .get() call.
pageSize
integer
(optional)
The size of the page to request up to a maximum of 10,000. If not provided, will load up to 10,000 Vitals. The pageSize of the initial page is used for subsequent pages.
pageToken
string
(optional)
If provided, will request a page with size less than or equal to the pageSize of the first requested page. If more than 10,000 Vitals have been requested, an ObjectsExceededLimit error will be thrown.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient/{primaryKey}/links/Vitals

from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient

def get_linked_Vitals(source: Patient):
    return source.vitals.iterate();

Filtering
The types of filtering you can perform depend on the types of the properties on a given object type. These filters can also be combined together via Boolean expressions to construct more complex filters.
Note that this endpoint leverages the underlying object syncing technology used for the object type. If Patient is backed by Object Storage V2, there is no request limit. If it is backed by Phonograph, there is a limit of 10,000 results – when more than 10,000 Patients have been requested, a ObjectsExceededLimit error will be thrown.
Parameters
where
SearchQuery
(optional)
Filter on a particular property. The possible operations depend on the type of the property.
orderBy
OrderByQuery
(optional)
Order the results based on a particular property. If using the SDK, you can chain the .where call with an orderBy call to achieve the same result.
pageSize
integer
(optional)
The size of the page to request up to a maximum of 10,000. If not provided, will load up to 10,000 Patients. The pageSize of the initial page is used for subsequent pages. If using the SDK, chain the .where call with the .page method.
pageToken
string
(optional)
If provided, will request a page with size less than or equal to the pageSize of the first requested page. If using the SDK, chain the .where call with the .page method.
POST
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient/search

from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient

page = client.ontology.objects.Patient.where(Patient.object_type.name.is_null()).iterate()

Types of search filters (SearchQuery)

Show


Aggregations
Perform aggregations on Patients
Parameters
aggregation
Aggregation[]
(optional)
Set of aggregation functions to perform. With the SDK, aggregation computations can be chained together with further searches using .where
groupBy
GroupBy[]
(optional)
A set of groupings to create for aggregation results
where
SearchQuery
(optional)
Filter on a particular property. The possible operations depend on the type of the property.
POST
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Patient/aggregate

from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient

numPatient = client.ontology.objects.Patient
    .where(~Patient.object_type.name.is_null())
    .group_by(Patient.object_type.name.exact())
    .count()
    .compute()

Types of aggregations (Aggregation)

Show


Types of group bys (GroupBy)

Show


Associated Action types
The following Action types are associated with this object type. These include any Actions that use this object type as an input parameter and Actions that create, modify or delete objects of this type. See the linked documentation for each Action type for more details on their behavior and how they can be used.

Edit Patient

Create Patient

Delete Patient


PROEntity
View in 

benshvartsman1 Ontology


Python


1.188

Description
Patient Reported Outcomes
Properties
Property
API Name

Type	Description
Id

id	

String
No description
Free Text

freeText	

String
No description
Patient
patient	

String
No description
Sentiment
sentiment	

String
No description
Submitted At
submittedAt	

Date
No description
Symptoms
symptoms	

Array of String
No description

Load single PROEntity
Parameters
primaryKey
string
The primary key of the PROEntity you want to fetch
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Proentity/{primaryKey}

result = client.ontology.objects.Proentity.get("primaryKey")

Load pages of PROEntities
Load a list of objects of a requested page size, after a given page token if present.
Note that this endpoint leverages the underlying object syncing technology used for the object type. If PROEntity is backed by Object Storage V2, there is no request limit. If it is backed by Phonograph, there is a limit of 10,000 results – when more than 10,000 PROEntities have been requested, a ObjectsExceededLimit error will be thrown.
Parameters
pageSize
integer
(optional)
The size of the page to request up to a maximum of 10,000. If not provided, will load up to 10,000 PROEntities. The pageSize of the initial page is used for subsequent pages.
pageToken
string
(optional)
If provided, will request a page with size less than or equal to the pageSize of the first requested page.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Proentity

result = client.ontology.objects.Proentity.page(page_size=30, page_token=None)
page_token = result.next_page_token
data = result.data

Load all PROEntities
Loads all PROEntities. Depending on the language, results could be a list with all rows or an iterator to loop through all rows.
Note that this endpoint leverages the underlying object syncing technology used for the object type. If PROEntity is backed by Object Storage V2, there is no request limit. If it is backed by Phonograph, there is a limit of 10,000 results – when more than 10,000 PROEntities have been requested, a ObjectsExceededLimit error will be thrown.
POST
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objectSets/loadObjects

objects_iterator = client.ontology.objects.Proentity.iterate()
objects = list(objects_iterator)

Load ordered results
Load an ordered list of PROEntities by specifying a sort direction for specific properties. When calling via APIs, sorting criteria are specified via the fields array. When calling via SDKs, you can chain multiple orderBy calls together. The sort order for strings is case-sensitive, meaning numbers will come before uppercase letters, which will come before lowercase letters. For example, "Cat" will come before "bat".
Parameters
field
string
The property you want to sort by. With the SDK, this is provided for you via a sortBy interface.
direction
asc
|
desc
The direction you want to sort in, either ascending or descending. With the SDK, this is provided via the asc() and desc() functions on the sortBy interface.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Proentity

from hospital_pro_patient_facing_app_sdk.ontology.objects import Proentity

client.ontology.objects.Proentity.where(~Proentity.object_type.free_text.is_null()).order_by(Proentity.object_type.free_text.asc()).iterate()

Load linked Patient
SELECT LINK TYPE



Patient

Load linked Patient from an instance of PROEntity
Parameters
primaryKey
string
Primary key of PROEntity to start from. If loading via the SDK, this is assumed via a previous .get() call.
pageSize
integer
(optional)
The size of the page to request up to a maximum of 10,000. If not provided, will load up to 10,000 Patients. The pageSize of the initial page is used for subsequent pages. Since this is a one sided link, the SDK will automatically fetch a single Patient.
pageToken
string
(optional)
If provided, will request a page with size less than or equal to the pageSize of the first requested page. If more than 10,000 Patients have been requested, an ObjectsExceededLimit error will be thrown. Since this is a one sided link, the SDK will automatically fetch a single Patient.
GET
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Proentity/{primaryKey}/links/Patient

from hospital_pro_patient_facing_app_sdk.ontology.objects import Proentity

def get_linked_Patient(source: Proentity):
    return source.check_ins.get()

Filtering
The types of filtering you can perform depend on the types of the properties on a given object type. These filters can also be combined together via Boolean expressions to construct more complex filters.
Note that this endpoint leverages the underlying object syncing technology used for the object type. If PROEntity is backed by Object Storage V2, there is no request limit. If it is backed by Phonograph, there is a limit of 10,000 results – when more than 10,000 PROEntities have been requested, a ObjectsExceededLimit error will be thrown.
Parameters
where
SearchQuery
(optional)
Filter on a particular property. The possible operations depend on the type of the property.
orderBy
OrderByQuery
(optional)
Order the results based on a particular property. If using the SDK, you can chain the .where call with an orderBy call to achieve the same result.
pageSize
integer
(optional)
The size of the page to request up to a maximum of 10,000. If not provided, will load up to 10,000 PROEntities. The pageSize of the initial page is used for subsequent pages. If using the SDK, chain the .where call with the .page method.
pageToken
string
(optional)
If provided, will request a page with size less than or equal to the pageSize of the first requested page. If using the SDK, chain the .where call with the .page method.
POST
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Proentity/search

from hospital_pro_patient_facing_app_sdk.ontology.objects import Proentity

page = client.ontology.objects.Proentity.where(Proentity.object_type.free_text.is_null()).iterate()

Types of search filters (SearchQuery)

Show


Aggregations
Perform aggregations on PROEntities
Parameters
aggregation
Aggregation[]
(optional)
Set of aggregation functions to perform. With the SDK, aggregation computations can be chained together with further searches using .where
groupBy
GroupBy[]
(optional)
A set of groupings to create for aggregation results
where
SearchQuery
(optional)
Filter on a particular property. The possible operations depend on the type of the property.
POST
/v2/ontologies/ontology-5a27f9af-c046-4295-b5cc-5a773fb36117/objects/Proentity/aggregate

from hospital_pro_patient_facing_app_sdk.ontology.objects import Proentity

numProentity = client.ontology.objects.Proentity
    .where(~Proentity.object_type.free_text.is_null())
    .group_by(Proentity.object_type.free_text.exact())
    .count()
    .compute()

Types of aggregations (Aggregation)

Show


Types of group bys (GroupBy)

Show


Associated Action types
The following Action types are associated with this object type. These include any Actions that use this object type as an input parameter and Actions that create, modify or delete objects of this type. See the linked documentation for each Action type for more details on their behavior and how they can be used.

Create PROEntity

Edit PROEntity

Delete PROEntity

