import React from "react";
import { AppHeader, Heading, Button, Textarea } from '@konturio/ui-kit';
import { Search16 } from '@konturio/default-icons';
import './report.css'

class ReportComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            status: [],
            filteredStatus: [],
            pipeline: null,
            columns: [
                { label: "Target name", accessor: "targetName", sortable: true },
                { label: "Last completed date", accessor: "lastTargetCompletionTime", sortable: true },
                { label: "Status", accessor: "targetType", sortable: true },
                { label: "Status date", accessor: "targetTime", sortable: true },
                { label: "Duration", accessor: "targetDuration", sortable: true },
                { label: "Log", accessor: "targetLog", sortable: false }
            ],
            sortField: "",
            order: "asc"
        };
    }

    componentDidMount() {
        fetch("report.json")
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        isLoaded: true,
                        status: result.status,
                        filteredStatus: result.status,
                        pipeline: result.pipeline
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            )
    }

    handleSortingChange = (accessor) => {
        const sortOrder =
            accessor === this.state.sortField && this.state.order === "asc" ? "desc" : "asc";
        this.setState({ sortField: accessor, order: sortOrder });
        this.handleSorting(accessor, sortOrder);
    };

    handleSorting = (sortField, sortOrder) => {
        if (sortField) {
            const sorted = [...this.state.filteredStatus].sort((a, b) => {
                if (a[sortField] === null) return 1;
                if (b[sortField] === null) return -1;
                if (a[sortField] === undefined || b[sortField] === undefined) return 0;

                return (
                    a[sortField].toString().localeCompare(b[sortField].toString(), "en", {
                        numeric: true,
                    }) * (sortOrder === "asc" ? 1 : -1)
                );
            });
            this.setState({
                filteredStatus: sorted
            });
        }
    };

    thead = () => {
        return (
            <thead>
                <tr className="header">
                    {this.state.columns.map(({ label, accessor, sortable }) => {
                        const cl = sortable
                            ? this.state.sortField === accessor && this.state.order === "asc"
                                ? "up"
                                : this.state.sortField === accessor && this.state.order === "desc"
                                    ? "down"
                                    : "default"
                            : "";
                        return (
                            <th
                                key={accessor}
                                onClick={sortable ? () => this.handleSortingChange(accessor) : null}
                                className={cl}
                            >
                                {label}
                            </th>
                        );
                    })}
                </tr>
            </thead>
        )
    }

    pipeline = (_pipeline) => {
        return (
            <table id="pipelineTable">
                <thead></thead>
                <tbody>
                    <tr>
                        <td><b>Present Status</b></td>
                        <td align="center"><b>{_pipeline.presentStatus}</b></td>
                    </tr>
                    <tr>
                        <td>Targets total</td>
                        <td align="center">{_pipeline.numberOfTargetsTotal}</td>
                    </tr>
                    <tr>
                        <td>Targets in progress</td>
                        <td align="center">{_pipeline.numberOfTargetsInProgress}</td>
                    </tr>
                    <tr>
                        <td>Targets failed</td>
                        <td align="center">{_pipeline.numberOfTargetsFailed}</td>
                    </tr>
                    <tr>
                        <td>Targets never started</td>
                        <td align="center">{_pipeline.numberOfTargetsNeverStarted}</td>
                    </tr>
                    <tr>
                        <td>Oldest completed target</td>
                        <td align="center">{this.formatDate(_pipeline.oldestCompletionTime)}</td>
                    </tr>
                </tbody>
            </table>
        )
    }

    status = (_status) => {
        return (
            <table id="statusTable" className="sortable">
                {this.thead()}
                <tbody>
                    {_status.map(item => (
                        <tr key={item.targetName} className={item.targetType}>
                            <td>{item.targetName}<p id='description'>{item.targetDescription}</p></td>
                            <td>{item.lastTargetCompletionTime ? this.formatDate(item.lastTargetCompletionTime) : '-'}</td>
                            <td>{item.targetType}</td>
                            <td>{item.targetTime ? this.formatDate(item.targetTime) : '-'}</td>
                            {/* toISOString Returns 2011-10-05T14:48:00.000Z From 11 to 19 gives hh:mm:ss */}
                            <td>{item.targetDuration ? new Date(item.targetDuration * 1000).toISOString().slice(11, 19) : '-'}</td>
                            {item.targetLog ? <td><a target='_blank' href={item.targetLog}>...</a></td> : <td>-</td>}
                        </tr>
                    ))}
                </tbody>
            </table>
        )
    }

    formatDate = (date) => {
        if (!date) {
            return ""
        } else {
            date = new Date(date);
            //YYYY-mm-dd hh:mm:ss adds 0 if needed
            return date == null
                ? ""
                : ("0" + date.getDate()).slice(-2) +
                "-" +
                ("0" + (date.getMonth() + 1)).slice(-2) +
                "-" +
                date.getFullYear() +
                " " +
                ("0" + date.getHours()).slice(-2) +
                ":" +
                ("0" + date.getMinutes()).slice(-2) +
                ":" +
                ("0" + date.getSeconds()).slice(-2);
        }
    }

    onFilter = (e) => {
        this.setState({
            filteredStatus: this.state.status
        })
        var filtered = this.state.status.filter((d) => {
            let filterText = e.target.value;
            if (filterText.startsWith('"') && filterText.endsWith('"')) {
                filterText = filterText.substring(1, filterText.length - 1)
                return d.targetName.toUpperCase() === filterText.toUpperCase().split(" ").join("_")
            }
            return d.targetName.toUpperCase().indexOf(filterText.toUpperCase().split(" ").join("_")) !== -1
        });
        this.setState({
            filteredStatus: filtered
        })
    }

    render() {
        const { error, isLoaded, filteredStatus, pipeline } = this.state;
        if (error) {
            console.log(error.message)
            return <div>Something went wrong parsing report</div>;
        } else if (!isLoaded) {
            return <div>Loading...</div>;
        } else {
            return (
                <div id="status">
                    <AppHeader title={"PIPELINE DASHBOARD"} />
                    <Heading type="heading-02">Pipeline Status</Heading>
                    {this.pipeline(pipeline)}
                    <Heading type="heading-02">Target status</Heading>
                    <Button variant="invert-outline" className="svgButton" onClick={(e) => {
                        e.preventDefault();
                        window.open("make.svg", "_blank");
                    }} >Status Chart</Button>
                    <Textarea className="searchInput" onChange={this.onFilter} message="Search for target name.." ><Search16 /></Textarea>
                    {this.status(filteredStatus)}
                </div>
            );
        }
    }
}

export default ReportComponent