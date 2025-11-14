"""
File Sorting Hat

Used for organizing files into pre-specified directories from environment
variables.
"""

from sys import argv

from .processing_factories import (
    MoveObjectSuperFactory,
    MoveObjectFactory
)
from .processing_objects import MoveObject, MoveResult, MoveStatus
from .extensions import validateSession



def printTitle(title: str) -> None:
    length = len(title)
    print("=" * length)
    print(title)
    print("=" * length)
    print()


def createObjects() -> list[MoveObject]:
    factory: MoveObjectFactory = \
        MoveObjectSuperFactory.chooseFactory()

    totalJobs = len(argv[1:])
    jobNumber = 0
    jobList: list[MoveObject] = []
    
    printTitle(f"Processing {totalJobs} files")
    
    for arg in argv[1:]:
        try:
            print(f"Job {jobNumber + 1}/{totalJobs}")
            print()
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
            jobNumber += 1
        finally:
            print("~ " * 10)
            print()
    
    print(f"Processed: {jobNumber}/{totalJobs}")
    print(f"Dropped: {totalJobs - jobNumber}")
    print()
    return jobList


def moveFiles(jobList: list[MoveObject]) -> list[MoveResult]:
    results: list[MoveResult] = []
    
    for job in jobList:
        try:
            job.move()
            result = MoveResult(job, MoveStatus.SUCCESS)
            results.append(result)
        except FileExistsError as e:
            result = MoveResult(job, MoveStatus.DESTINATION_EXISTS, e)
            results.append(result)
        except OSError as e:
            result = MoveResult(job, MoveStatus.FILE_IN_USE, e)
            results.append(result)
        except KeyboardInterrupt:
            break
        except Exception as e:
            result = MoveResult(job, MoveStatus.OTHER_ERROR, e)
            results.append(result)
        
    return results


def reportResults(results: list[MoveResult]) -> None:
    for result in results:
        print(result)


def processResults(results: list[MoveResult]) -> list[MoveResult]:
    ...


def main() -> None:
    validateSession()
    
    jobList = createObjects()
    moveResults = moveFiles(jobList)
    reportResults(moveResults)
    
    errorList: list[MoveObject] = []
    errors = len(errorList)
    duplicateList: list[MoveObject] = []
    duplicates = len(duplicateList)
    leave: bool = False
    
    while len(jobList) > 0 and not leave:
        startingJobs = len(jobList)
        print(f"Jobs to process: {startingJobs}")
        print(f"===============")
        
        # We'll be modifying the list, so work on a copy, not the original.
        for file in jobList.copy():
            try:
                print(f"{file.destination.name}: ", end="")
                file.move()
                print("moved")
                jobList.remove(file)
            except FileExistsError:
                print("duplicate (removing)")
                duplicateList.append(file)
                jobList.remove(file)
            except KeyboardInterrupt:
                print()
                leave = True
                break
            except Exception as e:
                print("error (removing)")
                print(f"\t{e}")
                errorList.append(file)
                jobList.remove(file)
        print()
        
        remainingJobs = len(jobList)
        duplicates = len(duplicateList)
        errors = len(errorList)
        print(f"Processed: {startingJobs - remainingJobs}/{startingJobs}")
        if duplicates: print(f"Duplicates: {duplicates}")
        if errors: print(f"Errors: {errors}")
        print()
        
        if remainingJobs:
            print(f"There are {remainingJobs} jobs left to process.")
            choice = None
            while choice != "y":
                choice = input("Process remaining jobs? [Y/n]:").lower() or "y"
                
                if choice == "n":
                    leave = True
            print()
    
    while duplicates:
        ...