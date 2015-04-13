# Introduction #

If you would like to add a new translation, follow these steps.


# Details #

  * Edit the file `pynguin.pro` in the project root directory
  * Add an entry in the TRANSLATIONS section for the new translation
    * Translation name/path should start with `data/translations/pynguin_`
    * Translation name/path should end with `.ts`
  * run `pylupdate4 pynguin.pro`
  * `pylupdate4` will create the `.ts` file in `data/translations`
  * Open the `.ts` file with Qt Linguist
    * Make translations and save your changes
    * File -> Release will create a `.qm` file
  * Test the translation
    * For example:
      * `LANG=es ./pynguin -d`