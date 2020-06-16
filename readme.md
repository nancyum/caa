#CAA Dissertation Project

This project deals with the College Art Association (CAA) dissertation roster, which has been published since 1963, first in print and then online only. This roster provides information about the changing shape of the field of art history over the past sixty years, through a collective profile of recent PhDs. Since 2004, the dissertation roster has been published by *caa.reviews* and is updated yearly. 

Professor Ken Chiu of Binghamton University wrote the script, caa.py, which scraped the data for completed dissertations from 2004 to 2018 [caa.reviews](http://www.caareviews.org/dissertations)

Nancy Um ran this script on March 29, 2020, which generated caa.csv. Some entries failed to populate due to formatting errors. The failed entries were saved separately. NU cleaned caa.csv with Open Refine, which resulted in the identification of a few more failed entries. NU generated a new file, which contained all of the failed entries, cleaned it, and then combined it with the entries in caa.csv.

The file caaTOTAL_OR.csv contains all of the entries from 2004 to 2018, including those that were harvested computationally and those that had to be entered by hand. The file subjects.csv was coded to classify some of the subject categories used for the dissertation roster, based on [CAA's standard breakdown](http://www.caareviews.org/about/dissertations).

The R markdown file, caa.Rmd, includes the scripts that were used to process the data, relying upon the tidyverse suite of packages, along with the tokenizers and tidytext packages. Plots were generated using ggplot. These visualizations pair with the article, Nancy Um, "Dissertations Completed and In Progress: One View of Art History's History," published as a special essay in caa.reviews in 2020. The figures are numbered accordingly.