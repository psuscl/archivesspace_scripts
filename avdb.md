# Processing AVDB sections

## The problem

The audiovisual database was imported to ArchivesSpace twice, but each import has separate metadata. In certain cases the metadata is inaccurate, e.g. location codes that no longer reflect the current shelf location for the items.

Offline work has been done to match records across the two AVDB collections. Our task is to overlay the metadata from AVDB-2 onto the AVDB record, so that we can do things like shelf-read the Cold Storage space, have one authoritative record for each program/title of AV content we have in the archives, and ultimately make the materials requestable to the public.

## Underlying assumptions

Different media types have different container/location strategies:

* Videocassette-based formats (VHS, Betacam, U-Matic, helical tapes) are itemized by cassette tape ([1:1](## "one-to-one") relationship between container and object)
* Audiocassettes are housed in share boxes ([1:n](## "one-to-many") relationship between container and object)
* Reel-to-reel tapes are itemized by reel ([1:1](## "one-to-one") relationship between container and object)
* 16mm reels are currently treated in a hybrid fashion; because their locations in the AVDB are based on _where_ they are stored on a shelf, we treat the left/right side of a shelf (and in some cases the front/back of a shelf) as if they are share boxes. This is temporary to facilitate completing the overlay process; we will revisit this in shelf reading.

## The process

All of this is commented in [avdb.py](avdb.py):

Going section by section, because each shelf section in Cold Storage contains different media types whose containers are handled differently:

1. download both records, based on the URI found in the 'uri' and 'avdb_uri' columns of the input spreadsheet
2. move to the next row if the AVDB-2 record is suppressed already (that means we already overlaid it)
3. if the spreadsheet has a flag indicating that the AVDB-2 title is preferred, save it to the AVDB record
4. clean up whitespace from AVDB notes
5. copy over all subject headings from AVDB-2 (we've already determined in pre-analysis that they're form/genre headings we like)
6. AVDB-2 has physical description notes indicating the extent of the item ("1" = 1 item; "20" = 20 items, etc.): convert these to proper ArchivesSpace extents and add them to the AVDB record
7. AVDB-2 has notes we want to keep in AVDB -- mostly these are scopecontent notes that describe the content of the objects, or general notes with appraisal outcomes, statements of responsibility, and so forth. we want to copy those over to the matching AVDB record.
8. create a top container from scratch based on the physical location note in AVDB-2 and link it to the matching AVDB record, *or* link to one that already exists in the database (we've previously run MySQL exports for Cold Storage locations and top containers and imported them as [pandas](https://pandas.pydata.org/) dataframes for matching purposes)

When we're done, suppress the AVDB-2 record and post the changes we've made to the AVDB record.
