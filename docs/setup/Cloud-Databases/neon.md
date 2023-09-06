# neon.tech
[neon.tech](https://neon.tech) is a service that kindly provides free hosted Postgres instances; they are unaffiliated to this project and have their own terms of service. Here's how you set one up for Simon:

## Create an account
Head on over to [neon.tech](https://neon.tech) to make an account.

## Create a new project

They seem to make the link quite small:

   <img src="https://github.com/Shabang-Systems/simon/assets/25516241/4aa77209-d910-4269-8ab6-8b77acc2e6cd" width="500"/>

## Configure your new project
Pick what you want for name and region, but **be sure to choose Postgres 15**.

   <img src="https://github.com/Shabang-Systems/simon/assets/25516241/5cba3e46-851f-4191-ba6e-d425de8c0532" width="500"/>

## Install PGVector 
Go to the SQL Editor and install the `vector` extension:

   ```sql
   CREATE EXTENSION vector;
   ```
   
   <img src="https://github.com/Shabang-Systems/simon/assets/25516241/99bc1ebd-44d4-4a34-9353-57783e9f4b18" height="300" />, then
   <img src="https://github.com/Shabang-Systems/simon/assets/25516241/4c3b0f4b-b097-44a3-ba9d-34ed712e2d8f" height="300" />

## Grab Your Configuration
Go back to the Dashboard and grab the database info you'll need to set up the Simon context:

   <img src="https://github.com/Shabang-Systems/simon/assets/25516241/f558b826-5b5a-43f6-9feb-d4b1fc5adbcb" width="500" />

   ![image](https://github.com/Shabang-Systems/simon/assets/25516241/e72bdec7-f6f9-48b0-89ca-bb0c6097276e)


Yay!

Now you're ready to [connect to the database](../../start.md#connect-to-database)
