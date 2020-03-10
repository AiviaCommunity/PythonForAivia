# Test Datasets for Aivia Scripts

It makes sense to test each Aivia recipe on four distinct cases with different image dimensions:

* 2D image
* 2D image with time
* 3D image
* 3D image with time

When you propose to add a recipe to our repository, we recommend testing it on each of the four examples images in this `/TestData/` folder to cover each of these use cases. To keep track of your work, please feel free to create an issue or pull request with check boxes for each of these test cases. Copy/paste the following code into the issue or pull request to format this correctly:

```
- [ ] Tested in 2D
- [ ] Tested in 2D+T
- [ ] Tested in 3D
- [ ] Tested in 3D+T
```

See an example of an enhancement issue for adding a new Python recipe to the repository [here](https://github.com/AiviaCommunity/PythonForAivia/issues/3).

Note that not all scripts need to pass these tests to be added. In some cases, your script may not apply to images of certain dimensions (e.g. an "in-place maximum intensity projection" recipe as shown here: ). This is OK! Please explain which cases are not applicable, and preferably use a try/catch or if/else structure to report these issues to the user in the Aivia log.
