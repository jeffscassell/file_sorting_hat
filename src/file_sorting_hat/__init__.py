"""
File Sorting Hat

Used for organizing files into pre-specified directories from environment
variables.
"""

from sys import argv

from fs_helpers import progressBar

from .processing_factories import (
    MoveObjectSuperFactory,
    MoveObjectFactory
)
from .processing_objects import (
    MoveObject,
    MoveResult,
    MoveStatus,
    recoverableErrors
)
from .extensions import validateSession



def printTitle(title: str) -> None:
    length = len(title)
    print("=" * length)
    print(title)
    print("=" * length)
    print()


def createObjects(args: list[str]) -> list[MoveObject]:
    factory: MoveObjectFactory = \
        MoveObjectSuperFactory.chooseFactory()

    totalJobs = len(args)
    currentJob = 0
    jobList: list[MoveObject] = []
    
    print("Note: stop in-taking files and begin processing with CTRL+C")
    print()
    
    for arg in args:
        try:
            print(f"Job {currentJob + 1}/{totalJobs}")
            file = factory.makeMoveObject(arg)
            jobList.append(file)
        except (ValueError, TypeError) as e:
            print(e)
            print("Dropping job.")
            print()
            continue
        except KeyboardInterrupt:
            print()
            print("Dropping remaing jobs.")
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
        except FileExistsError as e:
            result = MoveResult(job, MoveStatus.DUPLICATE, e)
            results.append(result)
        except OSError as e:
            result = MoveResult(job, MoveStatus.FILE_IN_USE, e)
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
    policies = {"built": "yes"}  # Only assign a policy if we need to do work.
    
    
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
    print("In case some files appear to be in use "
        "when attempting to move them:")
    
    choice = ""
    while choice not in ("y", "n"):
        choice = input("Retry move? [Y/n]: ").lower() or "y"
    print()
    
    if choice != "n":
        policies["inUse"] = choice


    return policies


def fixErrors(
    results: list[MoveResult],
    policies: dict[str, str]
) -> list[MoveResult]:
    
    # Return early if we don't need to do any work.
    # The policy is given 1 pair at instantiation, which means if it still
    # only has 1, it's empty.
    if len(policies) == 1:
        print("The selected policies indicate that no fixes are needed.")
        print()
        return results


    for result in progressBar(results):
        try:
            if result.status == MoveStatus.DUPLICATE:

                if policies.get("duplicates") == "d":
                    result.delete()

                if policies.get("duplicates") == "o":
                    result.overwrite()

            if result.status == MoveStatus.FILE_IN_USE:

                if policies.get("inUse") == "y":
                    result.move()

        except FileExistsError as e:
            result.status = MoveStatus.DUPLICATE
            result.exception = e
        except OSError as e:
            result.status = MoveStatus.FILE_IN_USE
            result.exception = e
        except BaseException as e:
            result.status = MoveStatus.OTHER_ERROR
            result.exception = e
    
    print()
    return results


def main() -> None:
    validateSession()
    
    args = argv[1:]
    printTitle(f"Processing {len(args)} files")
    jobList = createObjects(args)
    
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
                policies = getPolicies()
            
            printTitle("Fixing errors")
            moveResults = fixErrors(moveResults, policies)
            reportResults(moveResults)
        
    printTitle("Processing complete!")