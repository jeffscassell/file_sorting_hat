"""
File Sorting Hat

Used for organizing files into pre-specified directories from environment
variables.
"""

from sys import argv

from fs_helpers import progressBar

from .move_factories import (
    MoveObjectSuperFactory,
    MoveObjectFactory
)
from .move_objects import (
    MoveObject,
    MoveResult,
    MoveStatus,
    recoverableErrors
)
from .extensions import Config



def validateSession(args: list[str]) -> None:
    if len(args) == 1:
        raise ValueError("This script requires file arguments to function.")

    Config.load()
    Config.validatePath("VIDEO_PATH")
    Config.validatePath("OTHER_PATH")
    

def printTitle(title: str) -> None:
    length = len(title)
    print("=" * length)
    print(title)
    print("=" * length)
    print()


def buildObjects(
    args: list[str],
    factory: MoveObjectFactory
) -> list[MoveObject]:
    
    totalJobs = len(args)
    currentJob = 0
    jobList: list[MoveObject] = []

    print("[NOTE] Stop in-taking files and begin processing with CTRL+C")
    print()

    for arg in args:
        try:
            print(f"Job {currentJob + 1}/{totalJobs}")
            file = factory.makeMoveObject(arg)
            file.validate()
            file.buildOptions()
            jobList.append(file)
        except (ValueError, TypeError) as e:
            print(e)
            print("Dropping job.")
            print()
            continue
        except KeyboardInterrupt:
            print()
            print("<!> Dropping remaing jobs.")
            print()
            break
        else:
            currentJob += 1
        finally:
            print("~ " * 10)
            print()

    print(f"Processed: {currentJob}/{totalJobs}")
    print(f"Dropped: {totalJobs - currentJob}")
    print()
    return jobList


def moveFiles(jobList: list[MoveObject]) -> list[MoveResult]:
    results: list[MoveResult] = []

    for job in progressBar(jobList):
        try:
            job.move()
            result = MoveResult(job, MoveStatus.SUCCESS)
            results.append(result)
        except (FileExistsError, IsADirectoryError) as e:
            result = MoveResult(job, MoveStatus.DUPLICATE, e)
            results.append(result)
        except OSError as e:
            result = MoveResult(job, MoveStatus.DELETE_FAILURE, e)
            results.append(result)
        except KeyboardInterrupt:
            break
        except BaseException as e:
            result = MoveResult(job, MoveStatus.OTHER_ERROR, e)
            results.append(result)

    print()
    return results


def reportResults(results: list[MoveResult]) -> None:
    for result in results:
        # Don't display items that have already been successfully processed.
        if result.status == MoveStatus.PROCESSED:
            continue

        print(result)

        # Mark acceptably processed items as such.
        if result.status not in recoverableErrors:
            result.status = MoveStatus.PROCESSED

    print()


def recoverableErrorsExist(results: list[MoveResult]) -> bool:
    for result in results:
        if result.status in recoverableErrors:
            return True
    return False


def getPolicies() -> dict[str, str]:
    # Create initial pair so that we know a policy has been created later.
    policies = {"built": "yes"}  # Only assign more if we need to do work.


    # Get `duplicates` policy from user.
    print("In case some files already exist at their destination:")
    print("Delete the source files (d), overwrite destination (o), "
        "or ignore (i)?")

    choice = ""
    while choice not in "d o i".split():
        choice = input("[D/o/i]: ").lower() or "d"
    print()

    if choice != "i":
        policies["duplicates"] = choice


    # Get `inUse` policy from user.
    print("In case some source files appear to be in use "
        "when attempting to delete them:")

    choice = ""
    while choice not in ("y", "n"):
        choice = input("Retry delete? [Y/n]: ").lower() or "y"
    print()

    if choice != "n":
        policies["inUse"] = choice


    return policies


def fixErrors(
    results: list[MoveResult],
    policies: dict[str, str]
) -> list[MoveResult]:

    for result in progressBar(results):
        try:
            match result.status:
                case MoveStatus.DUPLICATE:
                    if policies.get("duplicates") == "d":
                        result.delete()

                    if policies.get("duplicates") == "o":
                        result.overwrite()

                case MoveStatus.DELETE_FAILURE:
                    if policies.get("inUse") == "y":
                        result.delete()

        except FileExistsError as e:
            result.status = MoveStatus.DUPLICATE
            result.exception = e
        except OSError as e:
            result.status = MoveStatus.DELETE_FAILURE
            result.exception = e
        except BaseException as e:
            result.status = MoveStatus.OTHER_ERROR
            result.exception = e

    print()
    return results


def main() -> None:
    validateSession(argv)

    args = argv[1:]
    printTitle(f"Processing {len(args)} files")
    factory = MoveObjectSuperFactory.chooseFactory()
    jobList = buildObjects(args, factory)

    printTitle(f"Moving {len(jobList)} files")
    moveResults = moveFiles(jobList)
    reportResults(moveResults)

    fix = "y"
    policies = {}
    while recoverableErrorsExist(moveResults) and fix != "n":
        fix = input("<!> There were some recoverable errors during "
            "processing, attempt to resolve them now? [Y/n]: ").lower() or "y"

        if fix == "y":
            print()

            if not policies:
                printTitle("Building error policies")
                policies = getPolicies()

            # Return early if we don't need to do any work.
            # The policy is given 1 pair at instantiation, which means if it still
            # only has 1, it's empty.
            if len(policies) == 1:
                print("The selected policies indicate that no fixes are needed.")
                update = ""
                while update not in ("y", "n"):
                    update = input("Update policies? [y/N]").lower() or "n"
                print()
                if update == "y":
                    printTitle("Re-building error policies")
                    policies = getPolicies()
                else:
                    continue

            printTitle("Fixing errors")
            moveResults = fixErrors(moveResults, policies)
            reportResults(moveResults)

        if fix == "n":
            print()

    printTitle("Processing complete!")